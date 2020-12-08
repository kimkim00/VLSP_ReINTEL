# -*- coding: utf-8 -*-
"""biLSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GWstEKmLrLsYzeNM-AJIIyL3RcqDjTut
"""

import numpy as np
import pandas as pd
from keras.layers import Dense, Input, LSTM, Bidirectional, Conv1D
from keras.layers import Dropout, Embedding
from keras.preprocessing import text, sequence
from keras.layers import GlobalMaxPooling1D, GlobalAveragePooling1D, concatenate, SpatialDropout1D
from keras.models import Model
from keras import backend as K
from keras.models import model_from_json
from keras.models import load_model

#download fasttext 
#! wget https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.vi.300.vec.gz

'''
import gzip
import shutil
with gzip.open('cc.vi.300.vec.gz', 'rb') as f_in:
    with open('cc.vi.300.vec', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
        '''

#download phow2v
#! wget https://public.vinai.io/word2vec_vi_words_300dims.zip

'''
from zipfile import ZipFile
zip = ZipFile('/content/word2vec_vi_words_300dims.zip')
zip.extractall()
'''

#download phow2v syllables
#! wget https://public.vinai.io/word2vec_vi_syllables_300dims.zip

'''
zip = ZipFile('word2vec_vi_syllables_300dims.zip')
zip.extractall()
'''

EMBEDDING_FILE= '/content/drive/MyDrive/vslp/cnn_lstm_biLSTM_GRU/cc.vi.300.vec'

max_features=2500
maxlen=500
embed_size=300

train=pd.read_csv('/content/drive/MyDrive/BERT/SA/VSLP_data/train_plus.csv')
train['post_message']=train['post_message'].fillna('none')
public_test = pd.read_csv('/content/drive/MyDrive/BERT/SA/VSLP_data/public_test.csv')
private_test = pd.read_csv('/content/drive/MyDrive/BERT/SA/VSLP_data/final_private_test_dropped_no_label - final_private_test_dropped_no_label.csv')

X_train = train["post_message"].fillna("none").values
y_train = train[['label']].values
X_test = private_test["post_message"].fillna("none").values

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42))

tokenizer = text.Tokenizer(num_words=max_features, lower=True)
tokenizer.fit_on_texts(list(X_train))

X_train = tokenizer.texts_to_sequences(X_train)
X_val = tokenizer.texts_to_sequences(X_val)

X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_val = sequence.pad_sequences(X_val, maxlen=maxlen)
print("create vector")

embeddings_index = {}
with open(EMBEDDING_FILE, encoding='utf8') as f:
    for line in f:
        values = line.rstrip().rsplit(' ')
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs

word_index = tokenizer.word_index
num_words = min(max_features, len(word_index) + 1)
embedding_matrix = np.zeros((num_words, embed_size))

for word, i in word_index.items():
    if i >= max_features:
        continue
  
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector

def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

inp = Input(shape=(maxlen,))
meta_input = Input(shape=(3505,))

x = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=True)(inp)
x = SpatialDropout1D(0.35)(x)

x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.15, recurrent_dropout=0.15))(x)
concat = concatenate([x, meta_input]) 
x = Conv1D(64, kernel_size=3, padding='valid', kernel_initializer='glorot_uniform')(x)

avg_pool = GlobalAveragePooling1D()(x)
max_pool = GlobalMaxPooling1D()(x)
x = concatenate([avg_pool, max_pool])

out = Dense(1, activation='sigmoid')(x)

model = Model(inp, out)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc',f1_m,precision_m, recall_m])

model.summary()

nlp_input = Input(shape=(maxlen,)) 
meta_input = Input(shape=(3505,))
meta_input2 = Input(shape=(1,))
emb = Embedding(max_features, embed_size, weights=[embedding_matrix], trainable=True)(nlp_input) 
nlp_out = Bidirectional(LSTM(128))(emb) 
concat = concatenate([nlp_out, meta_input, meta_input2]) 
classifier = Dense(32, activation='relu')(concat) 
output = Dense(1, activation='sigmoid')(classifier) 
model = Model(inputs=[nlp_input , meta_input, meta_input2], outputs=[output])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc',f1_m,precision_m, recall_m])

batch_size = 32
epochs =5
history = model.fit([X_train,user_train,X_trainn['len']], y_train, validation_data=([X_val,user_val, X_vall['len']], y_val), batch_size=batch_size, epochs=epochs, verbose=1)
# evaluate the model
loss, accuracy, f1_score, precision, recall = model.evaluate([X_val,user_val,X_vall['len']], y_val, verbose=0)

