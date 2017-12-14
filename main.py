import time
from math import ceil

from keras.callbacks import TensorBoard, ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from keras.models import load_model

# Utility code.
from src.load_data import load_data, get_test_data
# Data Generators
from src.log_spectrum_models.spectogram_generator import batch_generator as spectogram_batch_generator, \
    get_data_shape as get_spectogram_data_shape, test_batch_generator as spectogram_test_batch_generator
# Models
# Log spectrum based models
# Raw Audio based models
from src.raw_audio_models.VGG_raw_audio import VGGRawAudio
from src.raw_audio_models.raw_audio_generator import batch_generator as audio_batch_generator, \
    get_data_shape as get_audio_data_shape, test_batch_generator as audio_test_batch_generator
from src.results import write_results

# Mel cepstrum coefficient based models.

(x_train, y_train), (x_val, y_val), label_binarizer = load_data(path='./input/train/audio/')
test_set = get_test_data(path='./input/test/audio')

TRAIN = True
WRITE_RESULTS = False

# MODEL_TYPE = 'log_spectogram'
MODEL_TYPE = 'raw_audio'

batch_generator = 0
test_batch_generator = 0
get_data_shape = 0

if MODEL_TYPE == 'log_spectogram':
    batch_generator = spectogram_batch_generator
    test_batch_generator = spectogram_test_batch_generator
    get_data_shape = get_spectogram_data_shape
elif MODEL_TYPE == 'raw_audio':
    batch_generator = audio_batch_generator
    test_batch_generator = audio_test_batch_generator
    get_data_shape = get_audio_data_shape
elif MODEL_TYPE == 'mel_cepstrum':
    batch_generator = 0
    test_batch_generator = 0
    get_data_shape = 0
else:
    print('INVALID DATA GENERATOR SPECIFIED')

# model_instance = Conv5Dense3Model()
model_instance = VGGRawAudio()
# model_instance = Conv1Dense1Model()
# model_instance = VGG()

if TRAIN:
    model = model_instance.create_model(get_data_shape(x_train.iloc[0]))

    tensorboard = TensorBoard(log_dir='./logs/{}'.format(time.time()), batch_size=model_instance.BATCH_SIZE)
    checkpoint = ModelCheckpoint(model_instance.checkpoint_path, monitor='val_loss')
    early_stop = EarlyStopping(monitor='val_loss', patience=4, verbose=1, mode='auto')
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                                  patience=5, min_lr=0.0001)

    train_gen = batch_generator(x_train.values, y_train, batch_size=model_instance.BATCH_SIZE)
    valid_gen = batch_generator(x_val.values, y_val, batch_size=model_instance.BATCH_SIZE)

    model.fit_generator(
        generator=train_gen,
        epochs=model_instance.EPOCHS,
        steps_per_epoch=ceil(x_train.shape[0] / model_instance.BATCH_SIZE),
        validation_data=valid_gen,
        validation_steps=ceil(x_val.shape[0] / model_instance.BATCH_SIZE),
        callbacks=[tensorboard, checkpoint, early_stop]
    )
else:
    model = load_model(model_instance.checkpoint_path)

if WRITE_RESULTS:
    write_results(model, label_binarizer, test_batch_generator, test_set)
