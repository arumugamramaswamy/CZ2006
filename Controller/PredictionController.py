import os
from Controller.SearchController import SearchController
import argparse
import datetime
import torch
import Controller.model as model
import numpy as np

import Controller.util as util
import json

class PredictionController:


    # load tokenized features
    data = np.genfromtxt('./Controller/input/featureMatrix_train')
    test = np.genfromtxt('./Controller/input/featureMatrix_test')
    np.random.shuffle(data)
    X, y = data[:, :-1], data[:, -1]
    label = util.value2int_simple(y).astype("int") # using direction to label
    #label = to_categorical(value2int(y, clusters)).astype("int") # using quantile to label
    validation_ratio = 0.05
    X = X.astype('float32')
    D = int(data.shape[0] * validation_ratio)  # total number of validation data
    X_train, y_train, X_valid, y_valid = X[:-D], label[:-D], X[-D:], label[-D:]
    X_test, y_test = test[:, :-1], test[:, -1]

    #print("Positive News Ratio", sum(y_test > 0) * 1. / (sum(y_test > 0) + sum(y_test < 0)))
    X_test = X_test.astype('float32')
    y_test = util.value2int_simple(y_test).astype("int")

    @staticmethod
    def predict(searchResults):

        parser = argparse.ArgumentParser(description='CNN-based Financial News Classifier')
        # learning
        parser.add_argument('-lr', type=float, default=0.001, help='initial learning rate [default: 0.001]')
        parser.add_argument('-t', type=float, default=1, help='SGLD tempreture [default: 1]')

        parser.add_argument('-epochs', type=int, default=100, help='number of epochs for train [default: 100]')
        parser.add_argument('-batch-size', type=int, default=64, help='batch size for training [default: 64]')
        parser.add_argument('-save_dir', type=str, default='./Controller/input/models/', help='save thinning models')
        # model
        parser.add_argument('-dropout', type=float, default=0.5, help='the probability for dropout [default: 0.5]')
        parser.add_argument('-embed-dim', type=int, default=128, help='number of embedding dimension [default: 128]')
        parser.add_argument('-kernel-num', type=int, default=64, help='number of each kind of kernel')
        parser.add_argument('-kernel-sizes', type=str, default='2,3,4,5', help='comma-separated kernel size to use for convolution')
        parser.add_argument('-static', type=bool, default=True, help='fix the embedding')
        # device
        parser.add_argument('-device', type=int, default=-1, help='device to use for iterate data, -1 mean cpu [default: -1]')
        parser.add_argument('-no-cuda', action='store_true', default=False, help='disable the gpu')
        # option
        parser.add_argument('-predict', type=str, default=None, help='predict the sentence given')
        parser.add_argument('-eval', type=bool, default=False, help='evaluate testing set')
        parser.add_argument('-vocabs', type=int, default=6000, help='total number of vocabularies [default: 6000]')
        parser.add_argument('-words', type=int, default=40, help='max number of words in a sentence [default: 40]')
        parser.add_argument('-date', type=str, default='', help='date to be tested')

        args = parser.parse_args()

        # update args and print
        args.class_num = 2
        args.cuda = (not args.no_cuda) and torch.cuda.is_available(); del args.no_cuda
        args.kernel_sizes = [int(k) for k in args.kernel_sizes.split(',')]

        # model
        cnn = model.CNN_Text(args)
        if args.cuda:
            torch.cuda.set_device(args.device)
            cnn = cnn.cuda()

        mymodels, word2idx, stopWords = util.predictor_preprocess(cnn, args)

        newsDict = searchResults
        count = 0
        average = 0
        removeList = []
        for key,value in newsDict.items():
            title = key
            args.predict = title
            value = util.predict(args.predict, mymodels, word2idx, stopWords, args)
            if np.isnan(value):
                removeList.append(key)
                continue
            average += value
            count += 1
            newsDict[key]["Prediction Value"]= value

        for key in removeList:
            newsDict.pop(key)

        average = average / count
        return [newsDict, average]

if __name__ == "__main__":
    print(PredictionController.predict(SearchController.search("Apple","Last Day",5)))
    
    