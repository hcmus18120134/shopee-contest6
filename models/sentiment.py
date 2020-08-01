import torch
import torch.nn as nn
import torch.nn.functional as F
import transformers
from tqdm import tqdm
transformers.RobertaForSequenceClassification


class ClassiferBlockV5(nn.Module):

    def __init__(self, feature_dim, out_dim):
        super().__init__()
        hidden_dim = 128

        self.cls = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(feature_dim*2, out_dim),
        )

    def forward(self, x):
        seq_embed = x[0]

        apool = torch.mean(o1, 1)
        mpool, _ = torch.max(o1, 1)
        cat = torch.cat((apool, mpool), 1)

        res = self.cls(cat)
        return res


class ClassiferBlockV4(nn.Module):

    def __init__(self, feature_dim, out_dim):
        super().__init__()
        hidden_dim = 128
        self.lstm1 = nn.LSTM(feature_dim,
                             hidden_dim,
                             num_layers=1,
                             bidirectional=False,
                             batch_first=True)

        self.lstm2 = nn.LSTM(hidden_dim,
                             hidden_dim,
                             num_layers=1,
                             bidirectional=True,
                             batch_first=True)

        self.cls = nn.Sequential(
            nn.Linear(hidden_dim*2, hidden_dim),
            nn.Dropout(0.2),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, out_dim)
        )

    def forward(self, x):
        seq_embed = x[0]
        embeds, _ = self.lstm1(seq_embed)
        embeds, _ = self.lstm2(embeds)
        avg_pool = torch.mean(embeds, 1)
        res = self.cls(avg_pool)
        return res


class ClassiferBlockV3(nn.Module):

    def __init__(self, feature_dim, out_dim):
        super().__init__()
        hidden_dim = 128
        self.lstm = nn.LSTM(feature_dim,
                            hidden_dim,
                            num_layers=1,
                            bidirectional=True,
                            batch_first=True)

        self.cls = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.Dropout(0.2),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, out_dim)
        )

    def forward(self, x):
        seq_embed = x[0]
        seq_embed = seq_embed[:, 0, :]
        res = self.cls(seq_embed)
        return res


class ClassiferBlockV2(nn.Module):

    def __init__(self, feature_dim, out_dim):
        super().__init__()
        hidden_dim = 128

        self.lstm = nn.LSTM(out_dim,
                            hidden_dim,
                            num_layers=1,
                            bidirectional=True,
                            batch_first=True)

        self.token_cls = nn.Linear(feature_dim, out_dim)
        self.seq_cls = nn.Linear(hidden_dim * 2, out_dim)

    def forward(self, x):
        seq_embed = x[0]
        embeds = F.relu(self.token_cls(seq_embed))
        embeds, _ = self.lstm(embeds)

        avg_pool = torch.mean(embeds, 1)
        res = self.seq_cls(avg_pool)
        return res


class ClassiferBlockV1(nn.Module):

    def __init__(self, feature_dim, out_dim):
        super().__init__()
        hidden_dim = 128
        self.lstm1 = nn.LSTM(feature_dim,
                             hidden_dim,
                             num_layers=1,
                             bidirectional=False,
                             batch_first=True)

        self.lstm2 = nn.LSTM(hidden_dim,
                             hidden_dim,
                             num_layers=1,
                             bidirectional=True,
                             batch_first=True)

        self.drop = nn.Dropout(p=0.15)
        self.cls = nn.Sequential(
            nn.Linear(hidden_dim*2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, out_dim)
        )

    def forward(self, x):
        seq_embed = x[0]
        embeds, _ = self.lstm1(seq_embed)
        embeds, _ = self.lstm2(embeds)
        avg_pool = torch.mean(embeds, 1)
        res = self.cls(avg_pool)
        return res


class baseline_sentiment_bert(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()

        self.bert = transformers.BertModel.from_pretrained('bert-base-uncased')
        if freeze:
            self.freeze()
        self.feature_dim = self.bert.config.hidden_size

        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):

        _, pooled_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        logits = self.classifier(pooled_output)
        return logits

    def freeze(self):

        for param in self.bert.parameters():
            param.requires_grad = False


class xlnet_base(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.xlnet = transformers.XLNetModel.from_pretrained(
            "xlnet-base-cased")
        if freeze:
            self.freeze()
        self.feature_dim = self.xlnet.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.xlnet(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.xlnet.parameters():
            param.requires_grad = False


class xlnet_large(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.xlnet = transformers.XLNetModel.from_pretrained(
            "xlnet-large-cased")
        if freeze:
            self.freeze()
        self.feature_dim = self.xlnet.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.xlnet(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.model.parameters():
            param.requires_grad = False


class bert_base(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        # config baseline
        self.nclasses = nclasses
        self.bert = transformers.BertModel.from_pretrained("bert-base-uncased")
        if freeze:
            self.freeze()
        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs

        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


class bert_large(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.bert = transformers.BertModel.from_pretrained(
            "bert-large-uncased")
        if freeze:
            self.freeze()
        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


class bert_multi(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.bert = transformers.BertModel.from_pretrained(
            "bert-base-multilingual-uncased")
        if freeze:
            self.freeze()

        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


class bert_distil(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.bert = transformers.DistilBertModel.from_pretrained(
            "distilbert-base-uncased")
        if freeze:
            self.freeze()

        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


class bert_distil_multi(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.bert = transformers.DistilBertModel.from_pretrained(
            "distilbert-base-multilingual-cased")
        if freeze:
            self.freeze()

        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


class bert_mobile(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.bert = transformers.MobileBertModel.from_pretrained(
            "google/mobilebert-uncased")
        if freeze:
            self.freeze()

        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


class bert_roberta(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.bert = transformers.RobertaModel.from_pretrained(
            'distilroberta-base')
        if freeze:
            self.freeze()

        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


class bert_roberta_multi(nn.Module):
    """Baseline model"""

    def __init__(self, nclasses, freeze=False):
        super().__init__()
        self.nclasses = nclasses
        self.bert = transformers.XLMRobertaModel.from_pretrained(
            'xlm-roberta-base')
        if freeze:
            self.freeze()

        self.feature_dim = self.bert.config.hidden_size
        self.classifier = ClassiferBlockV1(self.feature_dim, nclasses)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embedded = outputs
        logits = self.classifier(embedded)
        return logits

    def freeze(self):
        for param in self.bert.parameters():
            param.requires_grad = False


if __name__ == "__main__":
    dev = torch.device('cpu')
    net = xlnet_sentiment(5).to(dev)
    print(net)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(net.parameters(), lr=0.001)

    tbar = tqdm(range(100))
    for iter_id in tbar:
        inps = {
            'input_ids': torch.rand(8, 100).long().to(dev),
            'attention_mask': torch.rand(8, 100).long().to(dev),
        }
        lbls = torch.rand(8, 1).long().to(dev)

        outs = net(inps['input_ids'], inps['attention_mask'])
        print(type(outs))
        print(type(lbls))
        loss = criterion(outs, lbls)
        loss.backward()
        optimizer.step()

        tbar.set_description_str(f'{iter_id}: {loss.item()}')
