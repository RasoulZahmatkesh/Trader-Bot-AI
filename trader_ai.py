import torch
import torch.nn as nn

class TraderAI(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 64),
            nn.ReLU(),
            nn.Linear(64, 3)
        )

    def forward(self, x):
        return self.net(x)

def ai_decision(model, data):
    tensor = torch.tensor(data, dtype=torch.float32)
    output = model(tensor)
    action = torch.argmax(output).item()
    return ['HOLD','BUY','SELL'][action]
