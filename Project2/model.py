import torch
import torch.nn as nn
import torchvision.models as models


class EncoderCNN(nn.Module):
    def __init__(self, embed_size):
        super(EncoderCNN, self).__init__()
        resnet = models.resnet50(pretrained=True)
        for param in resnet.parameters():
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-1]
        self.resnet = nn.Sequential(*modules)
        self.embed = nn.Linear(resnet.fc.in_features, embed_size)

    def forward(self, images):
        features = self.resnet(images)
        features = features.view(features.size(0), -1)
        features = self.embed(features)
        return features
    

class DecoderRNN(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers=1):
        #super(DecoderRNN, self).__init__()
        super().__init__()
        self.embedding = nn.Embedding(vocab_size,embed_size)
        self.lstm = nn.LSTM(input_size = embed_size,
                           hidden_size = hidden_size,
                           num_layers = num_layers,
                           batch_first = True
                           #dropout = dropout,
                           #bidirectional = True
                           )
        self.linear = nn.Linear(hidden_size,vocab_size)
        self.hidden = (torch.zeros(1,1,hidden_size),torch.zeros(1,1,hidden_size))
    
    def forward(self, features, captions):
        word_embedding = self.embedding(captions[:,:-1])
        embeddings = torch.cat((features.unsqueeze(1),word_embedding),1)
        lstm_output, self.hidden = self.lstm(embeddings)
        output = self.linear(lstm_output)
        return output

    def sample(self, inputs, states=None, max_len=20):
        #code inspired by https://github.com/muhyun/ and https://github.com/pdudero
        " accepts pre-processed image tensor (inputs) and returns predicted sentence (list of tensor ids of length max_len) "
        result = []
        hidden = None
        for i in range(max_len):
            output, hidden = self.lstm(inputs,hidden)
            output =  self.linear(output.squeeze(1))
            index = output.max(1)[1] #getting the max score for the caption.
            result.append(index.item())
            inputs = self.embedding(index).unsqueeze(1)
        return result