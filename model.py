import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Lambda, Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from keras.models import load_model
from keras.preprocessing import image
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras.preprocessing.image import ImageDataGenerator
from keras import optimizers
from sklearn.model_selection import train_test_split

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
SHAPE = (136, 203, 1)

def preprocess_data():
    data = pd.read_csv(('image_data.csv'), names=['id', 'label'], header=0)
    data['label'] = data['label'].apply(str)
    return data

def generate_model():
    model = Sequential()
    model.add(Lambda(lambda x: x/255.0, input_shape=SHAPE))
    model.add(Conv2D(filters=8,
                    kernel_size=(5, 5),
                    strides=2,
                    padding='same',
                    activation='relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(filters=16,
                    kernel_size=(3, 3),
                    padding='same',
                    activation='relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Flatten())
    model.add(Dropout(0.15))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(16, activation='relu'))
    model.add(Dense(5, activation='softmax'))
    model.summary()
    return model

def get_generator(data):
    # shuffle dataframe and partition train/test dataset
    data = data.sample(len(data), random_state=0)
    train, test = train_test_split(data, test_size=0.2)

    train_datagen = ImageDataGenerator()
    train_generator = train_datagen.flow_from_dataframe(
            dataframe=train,
            x_col='id',
            y_col='label',
            target_size=(136, 203),
            color_mode='grayscale',
            class_mode='sparse')

    validation_datagen = ImageDataGenerator()
    validation_generator = validation_datagen.flow_from_dataframe(
            dataframe=test,
            x_col='id',
            y_col='label',
            target_size=(136, 203),
            color_mode='grayscale',
            class_mode='sparse')

    return train_generator, validation_generator

def train(data, model):
    train_generator, validation_generator = get_generator(data)

    save_checkpoint = ModelCheckpoint(
            'best-model-{epoch:02d}-{val_loss:.2f}.h5',
            monitor='val_loss',
            save_best_only=True,
            mode='min')

    early_stoppage = EarlyStopping(
            monitor='val_loss',
            min_delta=0.003,
            mode='min',
            patience=2)

    optimizer = optimizers.Adam(lr=0.001)
    model.compile(
            optimizer=optimizer,
            metrics=['accuracy'],
            loss='sparse_categorical_crossentropy')

    model.fit_generator(
            train_generator,
            steps_per_epoch=1000,
            epochs=10,
            verbose=1,
            callbacks=[save_checkpoint, early_stoppage],
            validation_data=validation_generator,
            validation_steps=200)

def predict(image_path="media_assets/test3.png", model="model.h5", render=True):
    loaded_model = load_model(model)
    img = image.load_img(image_path, target_size=(136, 203), color_mode="grayscale")
    if render:
        plt.imshow(img)
        plt.show()
    img = np.array(np.expand_dims(img, axis=2))
    img = img[None, :]
    result = loaded_model.predict_classes(img)
    print("RESULT:      ", result[0])
    result = loaded_model.predict(img)
    print("PROB DISTR:  ", result)

if __name__ == "__main__":
    mode = 0
    if mode:
        data = preprocess_data()
        model = generate_model()
        train(data, model)
    else:
        predict("media_assets/test3.png", "model.h5", False)
