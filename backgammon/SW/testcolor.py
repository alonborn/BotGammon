import cv2
"""import numpy as np

# Global variables
distortion_factor = 0.1

def update_factor(key):
    global distortion_factor
    if key == ord('+'):
        distortion_factor += 0.01
    elif key == ord('-'):
        distortion_factor -= 0.01

# Callback function for mouse events
def display_factor(event, x, y, flags, param):
    global distortion_factor
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Current distortion factor: {distortion_factor}")

def distort_y(image, factor):
    height, width = image.shape[:2]

    # Create a grid of coordinates
    x_coords, y_coords = np.meshgrid(np.arange(width), np.arange(height))

    # Calculate the normalized factor along the X direction (from 0 to 1)
    normalized_factor = np.linspace(0, 1, width)

    # Calculate the distorted factor based on the given factor
    distorted_factor = normalized_factor * factor

    # Calculate the distorted Y coordinates
    distorted_y_coords = y_coords + (height - y_coords) * distorted_factor

    # Create the remap coordinates
    remap_coords = np.stack((x_coords, distorted_y_coords), axis=-1)

    # Use the remap function to apply distortion
    distorted_image = cv2.remap(image, remap_coords.astype(np.float32), None, interpolation=cv2.INTER_LINEAR)

    # Display the current factor on the image
    cv2.putText(distorted_image, f'Factor: {factor:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    return distorted_image


def distort_image(image, factor):
    # Rotate the image 90 degrees
    rotated_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    rotated_image = cv2.flip(rotated_image, 1)
    # Apply distortion along the Y direction using the same function
    distorted_rotated_image = distort_y(rotated_image, factor)
    distorted_rotated_image = cv2.flip(distorted_rotated_image, 1)
    # Rotate the distorted image back to the original orientation
    distorted_image = cv2.rotate(distorted_rotated_image, cv2.ROTATE_90_CLOCKWISE)
    
    return distorted_image



# Read the original image
image_path = "C:\\temp\\snapshot - calibration.jpg"
original_image = cv2.imread(image_path)

# Create a window and set the callback function for mouse events
cv2.namedWindow('Distorted Image')
cv2.setMouseCallback('Distorted Image', display_factor)

while True:
    # Apply gradual distortion to the image along the Y direction
    distorted_image = distort_image(original_image, distortion_factor)
    #distorted_image = distort_y(original_image, distortion_factor)

    # Display the distorted image
    cv2.imshow('Distorted Image', distorted_image)

    # Wait for a key event
    key = cv2.waitKey(1) & 0xFF

    # Check for key events
    if key == 27:  # Press 'Esc' to exit
        break
    else:
        # Update the distortion factor based on user input
        update_factor(key)

# Release the window and close all OpenCV windows
cv2.destroyAllWindows()


"""
"""cap=cv2.VideoCapture(0)
ret,image=cap.read()
cv2.imshow('Distorted Image', image)
cv2.waitKey(0) 
"""

"""def translate_numbers(input_list):
    result_list = []

    for sublist in input_list:
        translated_sublist = [min(max(0, x - 1), 23) if 1 <= x <= 24 else 25 if x == 0 or x == 25 else 26 for x in sublist]
        result_list.append(translated_sublist)

    return result_list

# Example usage
input_list = [[1, 4], [6, 9],[0,25],[26,27]]
translated_list = translate_numbers(input_list)

print("Original List:", input_list)
print("Translated List:", translated_list)"""

"""import cv2
import numpy as np

def find_dots(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Use the HoughCircles function to detect circles (dots)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=100,
        param2=30,
        minRadius=1,
        maxRadius=30,
    )

    if circles is not None:
        # Convert circle coordinates to integers
        circles = np.round(circles[0, :]).astype("int")

        # Ensure we have found at least two circles
        if len(circles) >= 2:
            # Sort circles based on their x-coordinate
            circles = circles[circles[:, 0].argsort()]

            # Return the coordinates of the two dots
            dot1 = circles[0][:2]
            dot2 = circles[1][:2]
            return dot1, dot2

    return None, None

def main():
    # Load the image from file
    image_path = 'C:\\temp\\dots.jpg'  # Replace with your image file path
    frame = cv2.imread(image_path)

    # Find the coordinates of the two dots
    dot1, dot2 = find_dots(frame)

    if dot1 is not None and dot2 is not None:
            # Calculate the angle to rotate the image
            angle = np.arctan2(dot2[1] - dot1[1], dot2[0] - dot1[0]) * 180 / np.pi

            # Rotate the image by the calculated angle
            rotated_frame = cv2.warpAffine(frame, cv2.getRotationMatrix2D((frame.shape[1] // 2, frame.shape[0] // 2), angle, 1.0), (frame.shape[1], frame.shape[0]))

            # Display the original and rotated images
            cv2.imshow("Original", frame)
            cv2.imshow("Rotated", rotated_frame)
            cv2.waitKey(0)  # Wait until any key is pressed before closing the windows

    else:
        print("Could not find two dots in the image.")

    # Close all windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()"""

import numpy as np
"""
def add_point(list_of_points, new_point, gen, d):
    # If the list_of_points is empty, create a new internal list with the new point and generation number
    if not list_of_points:
        list_of_points.append([[new_point, gen]])
        return list_of_points

    # Calculate the average of the first internal list
    average_point = np.mean([point[0] for point in list_of_points[0]], axis=0)

    # Calculate the distance between the average point and the new point
    distance = np.linalg.norm(np.array(average_point) - np.array(new_point))

    # Check if the distance is less than 'd'
    if distance < d:
        # Add the new point and generation number to the first internal list
        list_of_points[0].append([new_point, gen])
    else:
        # Create a new internal list with the new point and generation number
        list_of_points.append([[new_point, gen]])

    return list_of_points

# Example usage:
list_of_points = [[[[520, 119], 1], [[519, 118], 2]], [[[100, 100], 3], [[99, 99], 2]]]
new_point = [525, 125]
gen = 4
d = 10

list_of_points = add_point(list_of_points, new_point, gen, d)
print("1 Updated List of Points:", list_of_points)
new_point = [101, 102]
gen = 4
d = 10

list_of_points = add_point(list_of_points, new_point, gen, d)
print("2 Updated List of Points:", list_of_points)
new_point = [901, 302]
list_of_points = add_point(list_of_points, new_point, gen, d)

print("3 list_of_points:", list_of_points)
list_of_points = add_point(list_of_points, new_point, gen, d)
print("4 Updated List of Points:", list_of_points)


[[[[520, 119], 1], [[519, 118], 2], [[525, 125], 4]], [[[100, 100], 3], [[99, 99], 2]]]
[[[[520, 119], 1], [[519, 118], 2], [[525, 125], 4]], [[[100, 100], 3], [[99, 99], 2]], [[[101, 102], 4]]]
[[[[520, 119], 1], [[519, 118], 2], [[525, 125], 4]], [[[100, 100], 3], [[99, 99], 2]], [[[101, 102], 4]], [[[901, 302], 4]]]
[[[[520, 119], 1], [[519, 118], 2], [[525, 125], 4]], [[[100, 100], 3], [[99, 99], 2]], [[[101, 102], 4]], [[[901, 302], 4]], [[[901, 302], 4]]]


#rotated_frame = cv2.warpAffine(frame, cv2.getRotationMatrix2D((frame.shape[1] // 2, frame.shape[0] // 2), angle, 1.0), (frame.shape[1], frame.shape[0]))
[[556.2, 178.20001, 23.920002], [568.2, 52.2, 25.0], [685.80005, 97.8, 23.560001], [687.0, 606.60004, 25.720001], [851.4, 304.2, 29.320002], [958.2, 595.80005, 21.279999], [1173.0, 555.0, 25.36], [861.00006, 334.2, 24.04], [882.60004, 336.6, 28.0], [1023.00006, 559.80005, 22.6], [1089.0, 29.400002, 12.76], [1225.8, 561.0, 19.84], [886.2, 289.80002, 25.36], [1164.6001, 514.2, 14.68], ...]

"""
"""import numpy as np

# Create a 2D array
matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

# Calculate the mean along each axis
mean_axis0 = np.mean(matrix, axis=0)  # Mean along axis 0 (columns)
mean_axis1 = np.mean(matrix, axis=1)  # Mean along axis 1 (rows)

print("Mean along axis 0 (columns):", mean_axis0)
print("Mean along axis 1 (rows):", mean_axis1)"""

def parse_board(board_string):
    # Split the board string into individual components
    components = board_string.split()

    # Extract the board configuration
    board = components

    parsed_board = []

    # Parse each column and convert to tuple
    for col in board:
        if col == '0':
            parsed_board.append((0, 0))
        else:
            parsed_board.append((col[0], int(col[1:])))

    return parsed_board

def compare_boards(board1, board2, look_for_smaller=True):
    # Iterate through each position in both boards
    positions = []
    for i in range(len(board1)):
        # Check if color is the same and number of checkers in board1 is smaller than in board2
        if board1[i][0] == board2[i][0]:
            if look_for_smaller and board1[i][1] < board2[i][1]:
                positions.append(i)
            elif not look_for_smaller and board1[i][1] > board2[i][1]:
                positions.append(i)
    return positions

def create_tuples(larger_positions, smaller_positions):
    tuples = []

    # Iterate through the larger_positions list
    for i, larger_pos in enumerate(larger_positions):
        # Get the corresponding smaller position if it exists
        smaller_pos = smaller_positions[i] if i < len(smaller_positions) else -1
        tuples.append((larger_pos, smaller_pos))

    # Add tuples for remaining smaller positions
    for smaller_pos in smaller_positions[len(larger_positions):]:
        tuples.append((-1, smaller_pos))

    return tuples

# Example usage:
#board1 = [(0, 0), ('b', 2), (0, 0), (0, 0), (0, 0), (0, 0), ('w', 5), (0, 0), ('w', 3), (0, 0), (0, 0), (0, 0), ('b', 5), ('w', 5), (0, 0), (0, 0), (0, 0), (0, 0), ('b', 3), (0, 0), ('b', 5), (0, 0), (0, 0), (0, 0), ('w', 2), (0, 0)]
#board2 = [(0, 0), ('b', 2), (0, 0), (0, 0), (0, 0), (0, 0), ('w', 5), (0, 0), ('w', 2), (0, 0), ('b', 1), (0, 0), ('b', 4), ('w', 5), (0, 0), (0, 0), (0, 0), (0, 0), ('b', 3), (0, 0), ('b', 5), (0, 0), (0, 0), (0, 0), ('w', 2), (0, 0)]

expected_board = "0    b2 0 0 0 0 w5 0 w3 0 0  0   b5 w4 0   0  0  b3  0  b5 0  0   0 0  w2    0  "
actual_board = "0      b2 0 0 0 0 w5 0 w3 0 0  0   b5 w5 0   0  0  b3  0  b5 0  0   0 0  w2    0  "
#               "0     1  2 3 4 5 6  7 8  9 10 11  12 13 14  15 16 17 18  19 20 21 22 23 24   25  
board1 = parse_board(expected_board)
board2 = parse_board(actual_board)

smaller_positions = compare_boards(board1, board2,True)
larger_positions = compare_boards(board1, board2,False)
tuples = create_tuples(smaller_positions,larger_positions)

print("Tuples:", tuples)






