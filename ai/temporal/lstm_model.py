# AquaGuard AI - LSTM/GRU Temporal Behavior Model
import torch
import torch.nn as nn

class BehaviorClassifier(nn.Module):
    def __init__(self, input_size=16, hidden_size=128, num_layers=2,
                 num_classes=3, dropout=0.3, model_type="lstm"):
        super().__init__()
        self.model_type = model_type
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        rnn_cls = nn.LSTM if model_type == "lstm" else nn.GRU
        self.rnn = rnn_cls(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        out, _ = self.rnn(x)
        last = out[:, -1, :]
        return self.classifier(last)
