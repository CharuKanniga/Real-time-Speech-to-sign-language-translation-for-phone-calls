"""
ISL Sign Language Model Trainer — Fixed Version
================================================
Fixes:
  - Removed brightness_range (requires scipy — not needed)
  - Filters out 'archive' and non-letter folders from dataset
  - Works with your 33-class dataset (1-9, A-Z)

Dataset structure:
  dataset/
    train/
      A/  B/  C/ ... Z/   (and optionally 1/ 2/ ... 9/)

After training, saves:
  model/isl_model.h5
  model/class_names.json
  model/model_info.json
  static/signs/alphabet/a.jpg ... z.jpg  (one image per letter)
"""

import os, json, sys

# ── Check dependencies ──
try:
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    import matplotlib
    matplotlib.use('Agg')  # No GUI needed — saves plot to file
    import matplotlib.pyplot as plt
    print("✅ All ML libraries found.")
except ImportError as e:
    print(f"\n❌ Missing library: {e}")
    print("\nRun: pip install tensorflow numpy matplotlib pillow")
    sys.exit(1)

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
IMG_SIZE   = (64, 64)
BATCH_SIZE = 32
EPOCHS     = 15
TRAIN_DIR  = "dataset/train"
TEST_DIR   = "dataset/test"
MODEL_DIR  = "model"
os.makedirs(MODEL_DIR, exist_ok=True)

# Folders to ignore in dataset (not actual sign classes)
IGNORE_FOLDERS = {'archive', '.DS_Store', '__pycache__', 'Thumbs.db'}

# ───────────────────────────────────────────────
# STEP 1: CHECK & CLEAN DATASET
# ───────────────────────────────────────────────
def check_dataset():
    if not os.path.exists(TRAIN_DIR):
        print(f"\n❌ Dataset folder not found: {TRAIN_DIR}")
        print("""
HOW TO SET UP:
1. Download from: https://www.kaggle.com/datasets/prathumarikeri/indian-sign-language-isl
2. Extract the ZIP
3. Copy all letter folders (A/, B/ ... Z/) into:
       PD/dataset/train/
4. Run this script again.
        """)
        return False

    all_dirs = sorted(os.listdir(TRAIN_DIR))
    classes  = [d for d in all_dirs
                if os.path.isdir(os.path.join(TRAIN_DIR, d))
                and d not in IGNORE_FOLDERS]

    if not classes:
        print("❌ No valid class folders found in dataset/train/")
        return False

    total = sum(
        len([f for f in os.listdir(os.path.join(TRAIN_DIR, c))
             if f.lower().endswith(('.jpg','.jpeg','.png'))])
        for c in classes
    )
    print(f"✅ Found {len(classes)} classes: {classes}")
    print(f"   Total training images: {total}")

    # Warn about ignored folders
    ignored = [d for d in all_dirs if d in IGNORE_FOLDERS]
    if ignored:
        print(f"   ℹ️  Ignored folders: {ignored}")

    return True

# ───────────────────────────────────────────────
# STEP 2: DATA PIPELINE
# ───────────────────────────────────────────────
def build_data_pipeline():
    print("\n📦 Building data pipeline...")

    # NO brightness_range — it requires scipy
    train_gen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=False,  # Never flip hands (L ≠ mirrored L)
        zoom_range=0.1,
        validation_split=0.2
    )
    test_gen = ImageDataGenerator(rescale=1./255)

    train_ds = train_gen.flow_from_directory(
        TRAIN_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode='categorical', subset='training', seed=42
    )
    val_ds = train_gen.flow_from_directory(
        TRAIN_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode='categorical', subset='validation', seed=42
    )

    test_ds = None
    if os.path.exists(TEST_DIR) and os.listdir(TEST_DIR):
        test_ds = test_gen.flow_from_directory(
            TEST_DIR, target_size=IMG_SIZE,
            batch_size=BATCH_SIZE, class_mode='categorical'
        )

    class_names = list(train_ds.class_indices.keys())
    with open(f"{MODEL_DIR}/class_names.json", "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"   Classes ({len(class_names)}): {class_names}")

    return train_ds, val_ds, test_ds, class_names

# ───────────────────────────────────────────────
# STEP 3: BUILD CNN MODEL
# ───────────────────────────────────────────────
def build_model(num_classes):
    print(f"\n🏗️  Building CNN model for {num_classes} classes...")

    model = keras.Sequential([
        layers.InputLayer(shape=(*IMG_SIZE, 3)),  # 'shape' not 'input_shape'

        # Block 1
        layers.Conv2D(32, (3,3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3,3), padding='same', activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 2
        layers.Conv2D(64, (3,3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3,3), padding='same', activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 3
        layers.Conv2D(128, (3,3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.3),

        # Classifier head
        layers.Flatten(),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    model.summary()
    return model

# ───────────────────────────────────────────────
# STEP 4: TRAIN
# ───────────────────────────────────────────────
def train_model(model, train_ds, val_ds):
    print(f"\n🚀 Training for up to {EPOCHS} epochs...")
    print("   (This may take 10–30 minutes on CPU — be patient!)\n")

    callbacks = [
        keras.callbacks.ModelCheckpoint(
            f"{MODEL_DIR}/isl_model.h5",
            monitor='val_accuracy', save_best_only=True, verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=3, verbose=1, min_lr=1e-6
        ),
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=6,
            restore_best_weights=True, verbose=1
        )
    ]

    history = model.fit(
        train_ds, validation_data=val_ds,
        epochs=EPOCHS, callbacks=callbacks
    )
    return history

# ───────────────────────────────────────────────
# STEP 5: EVALUATE + SAVE
# ───────────────────────────────────────────────
def evaluate_and_save(model, history, test_ds, class_names):
    best_val = max(history.history['val_accuracy'])
    print(f"\n✅ Best Validation Accuracy: {best_val*100:.1f}%")

    test_acc = None
    if test_ds:
        _, test_acc = model.evaluate(test_ds, verbose=0)
        print(f"✅ Test Accuracy: {test_acc*100:.1f}%")

    info = {
        "model_file": "isl_model.h5",
        "class_names": class_names,
        "num_classes": len(class_names),
        "img_size": list(IMG_SIZE),
        "best_val_accuracy": round(best_val, 4),
        "test_accuracy": round(test_acc, 4) if test_acc else None,
        "epochs_trained": len(history.history['accuracy'])
    }
    with open(f"{MODEL_DIR}/model_info.json", "w") as f:
        json.dump(info, f, indent=4)
    print(f"📋 Model info saved: {MODEL_DIR}/model_info.json")

    # Save training plot (no GUI)
    try:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].plot(history.history['accuracy'], label='Train')
        axes[0].plot(history.history['val_accuracy'], label='Val')
        axes[0].set_title('Accuracy'); axes[0].set_xlabel('Epoch')
        axes[0].legend()
        axes[1].plot(history.history['loss'], label='Train')
        axes[1].plot(history.history['val_loss'], label='Val')
        axes[1].set_title('Loss'); axes[1].set_xlabel('Epoch')
        axes[1].legend()
        plt.tight_layout()
        plt.savefig(f"{MODEL_DIR}/training_plot.png", dpi=120)
        plt.close()
        print(f"📊 Plot saved: {MODEL_DIR}/training_plot.png")
    except Exception as e:
        print(f"⚠️  Plot skipped: {e}")

    return info

# ───────────────────────────────────────────────
# STEP 6: COPY SIGN IMAGES → static/signs/alphabet/
# ───────────────────────────────────────────────
def copy_signs_to_static():
    import shutil
    alpha_dest = "static/signs/alphabet"
    os.makedirs(alpha_dest, exist_ok=True)
    copied = 0

    for cls in sorted(os.listdir(TRAIN_DIR)):
        if cls in IGNORE_FOLDERS: continue
        cls_path = os.path.join(TRAIN_DIR, cls)
        if not os.path.isdir(cls_path): continue

        imgs = [f for f in os.listdir(cls_path)
                if f.lower().endswith(('.jpg','.jpeg','.png'))]
        if imgs:
            src = os.path.join(cls_path, imgs[0])
            dst = os.path.join(alpha_dest, f"{cls.lower()}.jpg")
            shutil.copy2(src, dst)
            copied += 1

    print(f"🖼️  Copied {copied} sign images → static/signs/alphabet/")
    print("   The call screen will now show real hand gesture photos!")

# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("   ISL Connect — Sign Language Model Trainer")
    print("=" * 55)

    if not check_dataset():
        sys.exit(1)

    train_ds, val_ds, test_ds, class_names = build_data_pipeline()
    model = build_model(len(class_names))
    history = train_model(model, train_ds, val_ds)
    info = evaluate_and_save(model, history, test_ds, class_names)
    copy_signs_to_static()

    print("\n" + "=" * 55)
    print("✅  TRAINING COMPLETE!")
    print(f"   Model: {MODEL_DIR}/isl_model.h5")
    print(f"   Val Accuracy: {info['best_val_accuracy']*100:.1f}%")
    print("\n▶  Now run:  python app.py")
    print("=" * 55)