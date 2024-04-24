
from PIL import Image
import os
import pandas as pd
import time
import cv2
import csv

from AuxFunctions import AuxFunctions
af = AuxFunctions ()

#from DiceTraining import DiceRecognizer


def predict_label(model, image_path):
    print ("Loading Torch...")
    from torchvision import transforms
    
    import torch  
    print ("Torch Loaded")
    # Preprocess the image
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])

    image = Image.open(image_path)
    image_tensor = transform(image).unsqueeze(0)  # Add batch dimension

    # Make the prediction
    with torch.no_grad():
        model.eval()
        output = model(image_tensor)

    # Convert the predicted label based on the specified mapping
    _, predicted = torch.max(output, 1)
    converted_label = convert_label(predicted.item())

    return converted_label

def load_model(model_path, num_classes=23):
    import torch
    import torch.nn as nn
    class DiceRecognizer(nn.Module):
    
        def __init__(self):
            super(DiceRecognizer, self).__init__()
            self.conv1 = nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1)
            self.relu1 = nn.ReLU()
            self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
            
            self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
            self.relu2 = nn.ReLU()
            self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
            
            self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
            self.relu3 = nn.ReLU()
            self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)
            
            self.fc1 = nn.Linear(128 * 8 * 8, 512)
            self.relu4 = nn.ReLU()
            self.fc2 = nn.Linear(512, 23)  # Adjust output size based on your classes

        def forward(self, x):
            x = self.conv1(x)
            x = self.relu1(x)
            x = self.pool1(x)
            
            x = self.conv2(x)
            x = self.relu2(x)
            x = self.pool2(x)
            
            x = self.conv3(x)
            x = self.relu3(x)
            x = self.pool3(x)
            
            x = x.view(-1, 128 * 8 * 8)
            x = self.fc1(x)
            x = self.relu4(x)
            x = self.fc2(x)
            return x

    
    # Define the model architecture
    model = DiceRecognizer()

    # Load the trained model state dictionary
    if torch.cuda.is_available():
        model.load_state_dict(torch.load(model_path))
    else:
        # If running on a CPU-only machine, load the model on the CPU
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    
    # Set the model to evaluation mode
    model.eval()

    return model

def convert_label(label):
    # Mapping between original and converted labels
    #21 - error
    #22 - only one dice
    label_mapping = {
    0: (1, 1), 1: (1, 2), 2: (1, 3), 3: (1, 4), 4: (1, 5),
    5: (1, 6), 6: (2, 2), 7: (2, 3), 8: (2, 4), 9: (2, 5),
    10: (2, 6), 11: (3, 3), 12: (3, 4), 13: (3, 5), 14: (3, 6),
    15: (4, 4), 16: (4, 5), 17: (4, 6), 18: (5, 5), 19: (5, 6), 20: (6, 6), 21 : (0,0) , 22: (0,0)
    }
    return label_mapping[label]

def evaluate_model(csv_file, model_path):
    # Load CSV file
    import torch
    df = pd.read_csv(csv_file)
    
    # Load the model
    loaded_model = load_model(model_path, num_classes=23)
    
    loaded_model.eval()  # Set the model to evaluation mode
    
    misclassified_images = []
    
    # Iterate through each row in the CSV
    for index, row in df.iterrows():
        image_path = row['filename']
        label = row['label']
        
        # Predict label for the image

        img_name = "C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice2\\" + image_path
        predicted_label = predict_label(loaded_model, img_name)
        
        # Compare the predicted label with the ground truth label
        if predicted_label != convert_label(label):
            misclassified_images.append((image_path,predicted_label,convert_label(label)))
        else:
            print (index)
    
    # Print misclassified images
    if misclassified_images:
        print("Misclassified images:")
        for image_path in misclassified_images:
            print(image_path)
    else:
        print("All images were classified correctly.")



"""# Example usage
csv_file = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice-augmented-new-scrambled.csv'
model_path = 'dice_recognizer_model-new.pth'
evaluate_model(csv_file, model_path)"""



def process_images_in_folder(model_path, folder_path, output_csv):
    # Prepare the model
    loaded_model = load_model(model_path, num_classes=23)
    
    loaded_model.eval()  # Set the model to evaluation mode

    # Initialize CSV writer
    with open(output_csv, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Image', 'Dice1', 'Dice2'])

        # Process each image in the folder
        for image_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, image_name)

            #img_name = "C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice2\\" + image_path
            predicted_label = predict_label(loaded_model, image_path)


            # Process the output, replace this logic with your model's actual output processing
            dice1, dice2 = predicted_label[0],predicted_label[1]

            # Write to CSV
            writer.writerow([image_name, dice1, dice2])

"""
# Example usage:
model_path = 'dice_recognizer_model-new.pth'  # Path to your trained model
image_path = 'C:\\dice\\176.jpg'  # Path to the image you want to predict

# Load the model
loaded_model = load_model(model_path)

# Make a prediction and convert the label
converted_label = predict_label(loaded_model, image_path)

# Print the converted label
print(f'The predicted label is: {converted_label}')"""


#process_images_in_folder("dice_recognizer_model.pth","C:\\dice_test\\","C:\\temp\dice_test_list")