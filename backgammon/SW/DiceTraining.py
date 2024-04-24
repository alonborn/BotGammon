from PIL import Image
import os
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from sklearn.model_selection import train_test_split

# Define a simple CNN model
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

# Define a custom dataset class with data augmentation
class DiceDataset(Dataset):
    
    def __init__(self, X_data, y_data, transform=None, train=True):
        self.X_data, self.y_data = X_data, y_data
        self.transform = transform
        self.train = train

    def __len__(self):
        return len(self.X_data)

    def __getitem__(self, idx):
        img_name = self.X_data.iloc[idx]
        
        img_name = "C:\\dice_set2\\" + str(img_name)
        #img_name = "C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice2\\" + str(img_name)
        image = Image.open(img_name)
        label = int(self.y_data.iloc[idx])

        if self.train:
            num_of_rot_allowed = 10
            # Apply random rotations during training
            angle = torch.randint(0, num_of_rot_allowed, size=(1,)).item() * (360/num_of_rot_allowed)
            image = image.rotate(angle)

        if self.transform:
            image = self.transform(image)

        return image, label

# Define transformations for the images with normalization
transform_train = transforms.Compose([
    transforms.RandomRotation(90),
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),  # Adjust normalization values
])

transform_test = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),  # Adjust normalization values
])

# Set device (CPU or GPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Function to load and split data, create DataLoader instances
def load_and_split_data(csv_file, test_size=0.2, batch_size=32, shuffle=True):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(df['filename'], df['label'], test_size=test_size, random_state=42)

    train_dataset = DiceDataset(X_train, y_train, transform=transform_train, train=True)
    test_dataset = DiceDataset(X_test, y_test, transform=transform_test, train=False)

    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle)
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_dataloader, test_dataloader

import os

def rename_files(folder_path, start_number):
    # Get the list of files in the folder
    files = os.listdir(folder_path)
    
    # Sort the files to ensure consistent renaming
    files.sort()
    
    # Counter for the file number
    number = start_number
    
    # Iterate through the files and rename them
    for file_name in files:
        # Check if the file is a regular file
        if os.path.isfile(os.path.join(folder_path, file_name)):
            # Split the file name and extension
            name, ext = os.path.splitext(file_name)
            
            # Construct the new file name with the number
            new_name = f"{number}.jpg"
            
            # Rename the file
            os.rename(os.path.join(folder_path, file_name), os.path.join(folder_path, new_name))
            
            # Increment the number for the next file
            number += 1

# Example usage
"""folder_path = "C:\\dice\\"
start_number = 3084  # Starting number for renaming
rename_files(folder_path, start_number)"""



def run_training():
    # Create instances of the model, loss function, and optimizer
    model = DiceRecognizer().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0005)

    # Load and split data
    #csv_file_path = r'C:\\Users\\user\\OneDrive\\arduino\\backgammon\\dice data\\dice - data-2.csv'
    #csv_file_path = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice-augmented-new-scrambled.csv'
    csv_file_path = 'C:\\temp\\dice_list_set2_label.csv'
    train_dataloader, test_dataloader = load_and_split_data(csv_file=csv_file_path)

    # Training loop
    num_epochs = 100
    for epoch in range(num_epochs):
        # Training
        model.train()
        for inputs, labels in train_dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        # Testing
        model.eval()
        test_loss = 0.0
        correct_predictions = 0

        with torch.no_grad():
            for inputs, labels in test_dataloader:
                inputs, labels = inputs.to(device), labels.to(device)

                outputs = model(inputs)
                loss = criterion(outputs, labels)
                test_loss += loss.item()

                _, predicted = torch.max(outputs, 1)
                correct_predictions += (predicted == labels).sum().item()

        average_test_loss = test_loss / len(test_dataloader.dataset)
        accuracy = correct_predictions / len(test_dataloader.dataset)

        print(f'Epoch [{epoch+1}/{num_epochs}], Train Loss: {loss.item():.4f}, Test Loss: {average_test_loss:.4f}, Test Accuracy: {accuracy:.4f}')

        # Save the trained model
        name = f'dice_recognizer_model-new-{epoch}.pth'
        torch.save(model.state_dict(), name)

run_training()

"""
1505
1547
1559
1576
1676
1946
2027
2344
2391
2449
2469
2556
2578
2856
2862
2910
3007
3050

"""



"""11	0
    12	1
    13	2
    14	3
    15	4
    16	5
    22	6
    23	7
    24	8
    25	9
    26	10
    33	11
    34	12
    35	13
    36	14
    44	15
    45	16
    46	17
    55	18
    56	19
    66	20"""
