import math
import re
import numpy as np
import cv2
import os
from PIL import Image, ImageDraw, ImageFont
import math

class AuxFunctions:
    def FindMissingNumber(self,directory_path, extension=".jpg"):
        files = [file for file in os.listdir(directory_path) if file.endswith(extension)]

        if not files:
            return 1

        numbers = [int(file.split('.')[0]) for file in files]
        numbers.sort()

        for i, number in enumerate(numbers):
            if i + 1 != number:
                return i + 1

        return numbers[-1] + 1

    def BoundingRect(self,center, radius):
        x, y = center
        left = x - radius
        top = y + radius
        right = x + radius
        bottom = y - radius
    
        return (left, top), (right, bottom)

    def CalculateSlopeAndIntercept(self,point1, point2):
        x1, y1 = point1
        x2, y2 = point2

        # Check if the points define a vertical line
        if x1 == x2:
            raise ValueError("Vertical line, undefined slope")

        # Calculate slope
        slope = (y2 - y1) / (x2 - x1)

        # Calculate y-intercept
        y_intercept = y1 - slope * x1

        return slope, y_intercept

    def FindIntersectionPointsTwoPoints(self, start_point, end_point, x_min, y_min, x_max, y_max):
        x1, y1 = start_point
        x2, y2 = end_point

        # Check for a vertical line
        if x1 == x2:
            if x_min <= x2 <= x_max and y_min <= min(y1, y2) <= y_max and y_min <= max(y1, y2) <= y_max:
                return [(x2, y_min), (x2, y_max)]
            else:
                return []

        # Check if the entire line is within the rectangle
        if x_min <= min(x1, x2) <= x_max and x_min <= max(x1, x2) <= x_max and \
        y_min <= min(y1, y2) <= y_max and y_min <= max(y1, y2) <= y_max:
            return []

        # Calculate the line equation coefficients
        slope = (y2 - y1) / (x2 - x1)
        y_intercept = y1 - slope * x1

        # Calculate x-values at y_min and y_max
        x_at_y_min = (y_min - y_intercept) / slope
        x_at_y_max = (y_max - y_intercept) / slope

        # Calculate y-values at x_min and x_max
        y_at_x_min = slope * x_min + y_intercept
        y_at_x_max = slope * x_max + y_intercept

        intersection_points = []

        # Check if the line crosses the rectangle horizontally
        if x_min <= x_at_y_min <= x_max and y_min <= y_at_x_min <= y_max:
            intersection_points.append((x_at_y_min, y_min))
        if x_min <= x_at_y_max <= x_max and y_min <= y_at_x_max <= y_max: 
            intersection_points.append((x_at_y_max, y_max))

        # Check if the line crosses the rectangle vertically
        if y_min <= min(y_at_x_min, y_at_x_max) <= y_max and x_min <= x_at_y_min <= x_max:
            intersection_points.append((x_at_y_min, y_at_x_min))
        if y_min <= max(y_at_x_min, y_at_x_max) <= y_max and x_min <= x_at_y_max <= x_max:
            intersection_points.append((x_at_y_max, y_at_x_max))

        return intersection_points

    def FindIntersectionPoints(self, slope, y_intercept, x_min, y_min, x_max, y_max):
        # Check for a vertical line
        if slope == float('inf') or slope == float('-inf'):
            if x_min <= x_max and x_min == x_max:
                return [(x_min, y_min), (x_min, y_max)]
            elif x_min >= x_max and x_max == x_min:
                return [(x_max, y_min), (x_max, y_max)]
            else:
                return []

        # Check for a horizontal line
        if slope == 0:
            if y_min <= y_max and y_min == y_max:
                return [(x_min, y_min), (x_max, y_min)]
            elif y_min >= y_max and y_max == y_min:
                return [(x_min, y_max), (x_max, y_max)]
            else:
                return []

        # Calculate x-values at y_min and y_max
        x_at_y_min = (y_min - y_intercept) / slope
        x_at_y_max = (y_max - y_intercept) / slope

        # Calculate y-values at x_min and x_max
        y_at_x_min = slope * x_min + y_intercept
        y_at_x_max = slope * x_max + y_intercept

        intersection_points = []

        # Check if the line crosses the rectangle horizontally
        if x_min <= x_at_y_min <= x_max:
            intersection_points.append((x_at_y_min, y_min))
        if x_min <= x_at_y_max <= x_max:
            intersection_points.append((x_at_y_max, y_max))

        # Check if the line crosses the rectangle vertically
        if y_min <= y_at_x_min <= y_max:
            intersection_points.append((x_min, y_at_x_min))
        if y_min <= y_at_x_max <= y_max:
            intersection_points.append((x_max, y_at_x_max))

        return intersection_points


    def IsLineCrossingRectangle(self,slope, y_intercept, x_min, y_min, x_max, y_max):
            # Calculate y-values at x_min and x_max
            y_at_x_min = slope * x_min + y_intercept
            y_at_x_max = slope * x_max + y_intercept

            # Check if the line crosses the rectangle
            if (y_min <= y_at_x_min <= y_max) or (y_min <= y_at_x_max <= y_max):
                return True
            else:
                return False
    
    def distance_between_lines2(self,m1, b1, distance):
        # Calculate the slope of the perpendicular line (negative reciprocal of m1)
        m_perpendicular = -1 / m1 if m1 != 0 else float('inf')

        # Calculate the y-coordinate of the point on the second line
        # that is at the given distance from the first line
        y2 = m_perpendicular * distance + b1

        # The distance between the lines in the Y direction is the absolute
        # difference in the y-coordinates of the two points on the lines
        distance_y = abs(y2 - b1)

        return distance_y

    def ParallelLines(self,p1, p2, distance):
        # Calculate the slope and y-intercept of the line passing through p1 and p2
        m_line = (p2[1] - p1[1]) / (p2[0] - p1[0])
        b_line = p1[1] - m_line * p1[0]

        dist = distance * math.sqrt(1+m_line*m_line)
        b1 = b_line + dist
        b2 = b_line - dist

        return m_line, b1,b2

    """def ParallelLines(self,point1, point2, distance):
        x1, y1 = point1
        x2, y2 = point2

        # Calculate the slope (m)
        if x1 == x2:
            # Vertical line, return x = constant
            return 0
        else:
            m = (y2 - y1) / (x2 - x1)

        # Calculate the y-intercept (b)
        b = y1 - m * x1

        # Calculate the y-intercepts for parallel lines
        b_left = b + distance
        b_right = b - distance

        return m,b_left,b_right"""
    
    def GetBoundingRectangle(self,coordinates, threshold):
        if not coordinates:
            return None

        # Extract x and y coordinates
        x_coords, y_coords = zip(*coordinates)

        # Calculate bounding rectangle with threshold
        min_x = min(x_coords) - threshold
        max_x = max(x_coords) + threshold
        min_y = min(y_coords) - threshold
        max_y = max(y_coords) + threshold

        # Return bounding rectangle as (min_x, min_y, max_x, max_y)
        return (min_x, min_y, max_x, max_y)

    def calculate_distance(self,point1, point2):
        x1, y1 = point1
        x2, y2 = point2

        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance


    def distance_point_to_line(self,x1, y1, x2, y2, x, y):
        # Calculate the coefficients of the line equation Ax + By + C = 0
        A = y2 - y1
        B = x1 - x2
        C = (x2 * y1) - (x1 * y2)

        # Calculate the distance using the formula
        distance = abs((A * x + B * y + C)) / math.sqrt(A ** 2 + B ** 2)
        return distance



    def distance_point_to_line(self,point, line_coefficients):
        # Formula for the perpendicular distance from a point to a line
        x0, y0 = point
        a, b, c = line_coefficients
        return abs(a * x0 + b * y0 + c) / math.sqrt(a**2 + b**2)


    def rotate_point_clockwise(self,point, angle_degrees):
        # Convert angle to radians
        angle_radians = math.radians(angle_degrees)

        # Extract coordinates of the point
        x, y = point

        # Calculate rotated coordinates
        x_rotated = x * math.cos(angle_radians) - y * math.sin(angle_radians)
        y_rotated = x * math.sin(angle_radians) + y * math.cos(angle_radians)

        return x_rotated, y_rotated

    def distance_between_lines(self,point1, point2, point3, point_nt):
        # Coefficients for L1
        x1, y1 = point1
        x2, y2 = point2
        a1 = y2 - y1
        b1 = x1 - x2
        c1 = x2 * y1 - x1 * y2

        # Coefficients for L3
        x3, y3 = point3
        a3 = y3 - y2
        b3 = x2 - x3
        c3 = x3 * y2 - x2 * y3

        # Distance from Pnt to L1 along L2
        distance_l1_to_pnt_along_l2 = self.distance_point_to_line(point_nt, (a1, b1, c1)) #y dimension

        # Distance from Pnt to L2 along L1
        distance_pnt_to_l2_along_l1 = self.distance_point_to_line(point_nt, (a3, b3, c3)) #x dimension

        if point_nt[0] < point2[0]:
            distance_pnt_to_l2_along_l1 = -distance_pnt_to_l2_along_l1
        
        """if point_nt[1] < point2[1]:
            distance_l1_to_pnt_along_l2 = -distance_l1_to_pnt_along_l2"""

        return distance_pnt_to_l2_along_l1,distance_l1_to_pnt_along_l2

    

    def ExtractGCodeValues(self,gcode_line):
        # Define the regular expression pattern
        pattern = r'G0 X(-?\d+(\.\d+)?)\s*Y(-?\d+(\.\d+)?)\s*(?:F(\d+(\.\d+)?))?'

        # Use re.match to find the match at the beginning of the string
        match = re.match(pattern, gcode_line)

        if match:
            # Extract values from the matched groups
            x_value = float(match.group(1))
            y_value = float(match.group(3))
            f_value = float(match.group(5)) if match.group(5) else None

            return (x_value, y_value), f_value

        return None  # Return None if no match is found

        
    def ExtractNumberFromString(self,input_string):
        # Use regular expression to find a number in the string
        match = re.search(r'\d+', input_string)
        
        # Check if a match is found
        if match:
            # Extract and return the matched number
            return int(match.group())
        else:
            # Return a default value or handle the case when no number is found
            return None
    
    def IsCloseTo(self,point,endpoint):
        if (endpoint[0]-point[0])**2 + (endpoint[1]-point[1])**2 < 40:
            return True
        return False
    
    def FindFurthestPointFromPoint1(self,point1, point2, x_coordinates):
        x1, y1 = point1
        x2, y2 = point2

        # Check if the line is vertical
        if x1 == x2:
            valid_points = [(x, (y1 + y2) / 2) for x in x_coordinates if x == x1]
        else:
            # Calculate the corresponding y-coordinates using the equation of the line
            valid_points = [
                (x, y1 + ((y2 - y1) / (x2 - x1)) * (x - x1)) for x in x_coordinates if (x1 <= x <= x2) or (x2 <= x <= x1)
            ]

        # Find the point with the maximum distance from point1
        furthest_point = max(valid_points, key=lambda p: abs(p[1] - y1), default=None)

        return furthest_point


    def FindPointOnLine(self,point1, point2, x):
        x1, y1 = point1
        x2, y2 = point2

        # Check if the line is vertical
        if x1 == x2:
            if x == x1:
                return (x, (y1 + y2) / 2)  # Any y-coordinate on the line for a vertical line
            else:
                return None

        # Check if x is outside the x-range of the line
        if x < min(x1, x2) or x > max(x1, x2):
            return None

        # Calculate the corresponding y-coordinate using the equation of the line
        y = y1 + ((y2 - y1) / (x2 - x1)) * (x - x1)
        return (x, y)

    def FindXForY(self,point1, point2, target_y):
        # Calculate the slope (m)
        slope = 0
        if (point2[0] - point1[0]) != 0:
            slope = (point2[1] - point1[1]) / (point2[0] - point1[0])
        else:
            slope = 9999999
        # Use the formula to find x for the given y
        x = ((target_y - point1[1]) / slope) + point1[0]
        return x
    
    def FindYForX(self,point1, point2, target_x):
        # Calculate the slope (m)
        slope = (point2[1] - point1[1]) / (point2[0] - point1[0])

        # Use the slope-intercept form to find y for the given x
        y = slope * (target_x - point1[0]) + point1[1]
        return y

    def DrawDashedLine(image, start_point, end_point, color, thickness=1, dash_length=10.):
        # Calculate the length of the line segment
        line_length = np.linalg.norm(np.array(end_point) - np.array(start_point))

        # Calculate the number of dashes needed
        num_dashes = int(line_length / dash_length) # type: ignore

        # Calculate the step size for each dash
        step_size = np.array((end_point[0] - start_point[0], end_point[1] - start_point[1])) / num_dashes

        # Draw each dash
        current_point = np.array(start_point, dtype=int)
        for _ in range(num_dashes):
            cv2.line(image, tuple(current_point), tuple((current_point + step_size).astype(int)), color, thickness) # type: ignore
            current_point += 2 * step_size  # Skip a dash

    def ConcatenateCommand(self,commands):
        # Use '%' as the delimiter to join the strings
        result_string = '^'.join(commands)
        return result_string
    
    def orientation(self,x1, y1, x2, y2, x3, y3):
        val = (y2 - y1) * (x3 - x2) - (x2 - x1) * (y3 - y2)
        if val == 0:
            return 0  # Collinear
        return 1 if val > 0 else 2  # Clockwise or counterclockwise

    def on_segment(self,x1, y1, x2, y2, x, y):
        return (
            (x <= max(x1, x2) and x >= min(x1, x2))
            and (y <= max(y1, y2) and y >= min(y1, y2))
        )

    def DoLinesIntersect(self,line, rectangle):
        rect_x1, rect_y1 = rectangle[0]  # Top-left corner of the rectangle
        rect_x2, rect_y2 = rectangle[1]  # Bottom-right corner of the rectangle

        # Check if the line intersects with any of the rectangle segments
        if (
            self.is_segment_intersection(line, [(rect_x1, rect_y1), (rect_x2, rect_y1)]) or
            self.is_segment_intersection(line, [(rect_x1, rect_y2), (rect_x2, rect_y2)]) or
            self.is_segment_intersection(line, [(rect_x1, rect_y1), (rect_x1, rect_y2)]) or
            self.is_segment_intersection(line, [(rect_x2, rect_y1), (rect_x2, rect_y2)])
        ):
            return True
        else:
            return False
    
    def is_segment_intersection(self,seg1, seg2):
        # Helper function to check if two line segments intersect
        x1, y1 = seg1[0]
        x2, y2 = seg1[1]
        x3, y3 = seg2[0]
        x4, y4 = seg2[1]
        return (
            min(x1, x2) <= max(x3, x4) and
            max(x1, x2) >= min(x3, x4) and
            min(y1, y2) <= max(y3, y4) and
            max(y1, y2) >= min(y3, y4) and
            (x1 - x2) * (y3 - y1) != (x3 - x1) * (y1 - y2)
        )

    
    def RotateImage(self,image, angle_degrees):
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Calculate the rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle_degrees, 1)
        
        # Apply rotation to the image
        rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))
        
        return rotated_image
    
    def GetQuadrantColumns(self,column):
        if 0 <= column <= 5:
            return range(0,6)
        elif 6 <= column <= 11:
            return range(6,12)
        elif 12 <= column <= 17:
            return range(12,18)
        elif 18 <= column <= 23:
            return range(18,24)
        else:
            # Handle other cases as needed
            return None

    #returns the quadrant where the column is 
    #top-right- 0
    #top-left - 1
    #bottom-left- 2
    #bottm-right-3           
    def GetQuadrant(self,column):
        if 0 <= column <= 5:
            return 0
        elif 6 <= column <= 11:
            return 1
        elif 12 <= column <= 17:
            return 2
        elif 18 <= column <= 23:
            return 3
        else:
            # Handle other cases as needed
            return None
        
    #returns 1 if in upper columns or 0 if bottom columns
    def GetColumnSide (self,column):
        return column < 12
    
    #return if columns are at the same side (up or down)
    def AreColumnsSameSide(self,column1,column2):
        return self.GetColumnSide(column1) == self.GetColumnSide(column2)
    
    def AreColumnsSameHalf(self,column1,column2):
        if  self.GetQuadrant(column1) in (0,3) and self.GetQuadrant(column2) in (0,3) or \
            self.GetQuadrant(column1) in (1,2) and self.GetQuadrant(column2) in (1,2):
            return True
        return False
    def AreColumnsSameQuadrant(self, column1, column2):
        return self.GetQuadrant(column1) == self.GetQuadrant(column2)

    #assuming columns are at the same quardart, is origin_column right to the target or not (left to it)
    def IsColumnRightTo(self,origin_column,target_column):
        if self.GetColumnSide(origin_column) == 0:
            return target_column<origin_column
        else:
            return target_column>origin_column

    def TextToImage(self,image, strings, top_left_point, font_size=20, highlighted_line=None, n=None):
        if image is None:
            return
        # Convert the NumPy array to a PIL Image
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)

        # Set the font (you can change the font file and size as needed)
        font = ImageFont.load_default()  # You may need to specify a font file path
        font_size = font_size
        font = ImageFont.truetype("arial.ttf", font_size)

        # Set the background color and text color
        background_color = (0, 0, 0)  # Black background
        text_color = (255, 255, 255)  # White text
        highlight_color = (128, 128, 128)  # Grey background for highlighted line

        # Print the first n lines on the image
        if n is None:
            n = len(strings)

        for i in range(min(n, len(strings))):
            line = strings[i]
            y_position = top_left_point[1] + i * font_size

            # Determine the background color based on whether the line is highlighted
            if i == highlighted_line:
                background_rect = [top_left_point[0], y_position, top_left_point[0] + 500, y_position + font_size]
                draw.rectangle(background_rect, fill=highlight_color) # type: ignore
            else:
                background_rect = [top_left_point[0], y_position, top_left_point[0] + 500, y_position + font_size]
                draw.rectangle(background_rect, fill=background_color)

            # Print the line
            draw.text((top_left_point[0], y_position), line, font=font, fill=text_color)

        # Convert the PIL Image back to a NumPy array
        image_with_text = np.array(pil_image)

        return image_with_text

    filename = "C:\\temp\\snapshot.jpg"
    def TakeSnapshot(self):
        if self.IsSnapshotAvailable():
            return
        cap=cv2.VideoCapture(0)
        ret,image=cap.read()
        cv2.imwrite(self.filename, image)
        cap.release()

    def IsSnapshotAvailable(self):
        return os.path.exists(self.filename)
    
    def GetSnapshot(self):
         return cv2.imread(self.filename)
    
    def GetFurthestPoint(self,given_point, point_list):
        if not point_list:
            return None  # Return None for an empty list

        max_distance = float('-inf')
        furthest_point = None

        for point in point_list:
            distance = self.calculate_distance(given_point, point)
            if distance > max_distance:
                max_distance = distance
                furthest_point = point

        return furthest_point
    

    def DistortImageX(self,image, factor):
        # Rotate the image 90 degrees
        rotated_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        rotated_image = cv2.flip(rotated_image, 1)
        # Apply distortion along the Y direction using the same function
        distorted_rotated_image = self.DistortImageY(rotated_image, factor)
        distorted_rotated_image = cv2.flip(distorted_rotated_image, 1)
        # Rotate the distorted image back to the original orientation
        distorted_image = cv2.rotate(distorted_rotated_image, cv2.ROTATE_90_CLOCKWISE)
    
        return distorted_image
    
    def DistortImageY(self,image, factor):
        flipped = cv2.flip(image, -1)
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
        distorted_image = cv2.remap(flipped, remap_coords.astype(np.float32), None, interpolation=cv2.INTER_LINEAR)

        # Display the current factor on the image
        cv2.putText(distorted_image, f'Factor: {factor:.3f}', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        distorted_image = cv2.flip(distorted_image, -1)
        return distorted_image
    
    import math

    def FindClosestPoint(self,target_point, point_list):
        closest_distance = float('inf')
        closest_point = None

        for index, point in point_list:
            distance = self.calculate_distance(target_point, point)
            if distance < closest_distance:
                closest_distance = distance
                closest_point = point

        return closest_point
    
    def IsBeforeStart (self,pos,start,end):
        if start < end and pos < start:
            return True
        if start > end and pos > start:
            return True
        return False
    def IsAfterEnd (self,pos,start,end):
        if start < end and pos > end:
            return True
        if start > end and pos < end:
            return True
        return False
    
    def FindClosestMidPosition(self, numbers, min_free_space,radius,middle):
        if not numbers or len(numbers) < 2:
            return None

        sorted_numbers = sorted(numbers)
        #middle = (sorted_numbers[0] +sorted_numbers[len(numbers)-1])/2.
        valid_boundaries = []

        for i in range(len(sorted_numbers) - 1):
            start_boundary = sorted_numbers[i]
            end_boundary = sorted_numbers[i + 1]
            free_space = end_boundary - start_boundary

            if free_space > min_free_space:
                mid_point = (start_boundary + end_boundary) / 2
                valid_boundaries.append({
                    'boundary': [start_boundary+radius, end_boundary-radius],
                    'distance_to_middle': abs(mid_point - middle)
                })

        if not valid_boundaries:
            return None

        # Sort by distance to middle and return the closest one(s)
        valid_boundaries.sort(key=lambda x: x['distance_to_middle'])
        closest_distance = valid_boundaries[0]['distance_to_middle']
        closest_boundary = valid_boundaries[0]['boundary']

        ret_val = middle 
        if middle < closest_boundary[0] + (radius/2):
            ret_val = closest_boundary[0] + (radius/2)
        if middle > closest_boundary[1] - (radius/2):
            ret_val = closest_boundary[1] - (radius/2)
    

        return ret_val

    
    def OtherColor(self,color):
        return 'b' if color == 'w' else 'w'
    
    def TranslateAutoMoveToBoard(self, input_list):
        #1-->24 --> 0-->23
        #0 --> 25 (black bar)
        #25 --> 26 (white bar)
        #26,27 --> 26 (home)

        # Initialize an empty list to store the results
        result_list = []

        # Iterate through each sublist in the input_list
        for sublist in input_list:
            # Translate each element in the sublist based on the updated conditions
            translated_sublist = [
                25 if x == 0 else 26 if x == 25 else 27 if x in (26, 27) else min(max(0, x - 1), 23)
                for x in sublist
            ]
            
            # Append the translated sublist to the result_list
            result_list.append(translated_sublist)

        # Return the final result_list
        return result_list

    def FindRotationMatrix(self,point1,point2,frame):
        if point1 is not None and point2 is not None:
            # Calculate the angle to rotate the image
            angle = np.arctan2(point2[1] - point1[1], point2[0] - point1[0]) * 180 / np.pi

            # Rotate the image by the calculated angle
            rotation_matrix = cv2.getRotationMatrix2D((frame.shape[1] // 2, frame.shape[0] // 2), angle, 1.0)
            return rotation_matrix
        else:
            print("Could not find two dots in the image.")
        return None
    
   
    def DrawLine (self,image,m,b):
        width = 1300
        x_values = np.linspace(0, width, 100)  # 100 points between 0 and 1300
        y_values = m * x_values + b

        points = np.array(list(zip(x_values.astype(int), y_values.astype(int))), np.int32)
        points = points.reshape((-1, 1, 2))

        cv2.polylines(image, [points], isClosed=False, color=(255, 255, 255), thickness=2)

    def draw_circles(self,image, circle_centers, radius,color):
        for center in circle_centers:
            cv2.circle(image, (int(center[0]),int(center[1])), int(radius), color, thickness=2)


    def distance_to_line(self,x, y, m, b):
        return abs(m * x - y + b) / math.sqrt(m**2 + 1)

    """def line_circle_intersection(self,m, b, circles,rad):
        intersecting_circles = []

        for circle in circles:
            cx, cy = circle
            distance = self.distance_to_line(cx, cy, m, b)

            if distance <= rad:
                intersecting_circles.append(circle)

        return intersecting_circles"""
    

    def IsLineIntersectsWithCircle(self,m,b,cirlces,rad,p1,p2):
        return True if len(self.line_circle_intersection(m,b,cirlces,rad,p1,p2)) > 0 else False
        
    def circles_intersect(self,circles1, circles2, radius):
        for circle1 in circles1:
            for circle2 in circles2:
                if self.are_circles_intersecting(circle1, circle2, radius):
                    return True
        return False

    def are_circles_intersecting(self,center1, center2, radius):
        # Calculate the distance between the centers of the two circles
        distance_between_centers = math.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

        # Check if the distance is less than the sum of the radii
        return distance_between_centers < 2 * radius

    def generate_internal_points(self,point1, point2, distance):
        # Convert the points to NumPy arrays for easy vector operations
        p1 = np.array(point1)
        p2 = np.array(point2)

        # Calculate the direction vector between the two points
        direction_vector = p2 - p1

        # Normalize the direction vector
        normalized_direction = direction_vector / np.linalg.norm(direction_vector)

        # Calculate the number of points to generate
        num_points = int(np.linalg.norm(direction_vector) / distance)

        # Generate internal points along the line as tuples
        internal_points = [tuple(p1 + i * normalized_direction * distance) for i in range(num_points + 1)]

        return internal_points
    
    def mean_max_values_around_point(self,gray_image, center_point, r):

        h, w = gray_image.shape

        # Extracting the coordinates of the center point
        center_x, center_y = center_point

        # Creating a mask for the rectangular region around the center point
        start_x = max(0, int(center_x - r))
        end_x = min(w, int(center_x + r))
        start_y = max(0, int(center_y - r))
        end_y = min(h, int(center_y + r))

        # Initializing the sum
        sum_count = 0

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Calculate the distance from the current pixel to the center
                distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)

                # Check if the pixel is within the radius
                if distance < r:
                    # Check if the pixel value is close to white (e.g., above a threshold)
                    if gray_image[y, x] < 80:  # Adjust the threshold as needed
                        sum_count += 1
                    # You can add additional conditions for black pixels if needed

        #print (f"{center_point} sum = {sum_count}")
        return sum_count
    
    import math

    def get_points_until_distance(self, points, max_dist, start_from_highest=True):
        # Sort points based on y position, either in ascending or descending order
        sorted_points = sorted(points, key=lambda x: x[0][1], reverse=start_from_highest)

        # Initialize the result list
        result = []

        # Iterate through sorted points
        for i in range(len(sorted_points)):
            current_point, _ = sorted_points[i]

            # Determine the next_point or set a large positive/negative value if at the last point
            next_point = sorted_points[i + 1][0] if i < len(sorted_points) - 1 else (10000, 10000) if start_from_highest else (-10000, -10000)

            # Calculate distance between current and next points
            distance = abs(int(next_point[1]) - int(current_point[1]))

            # Check if the distance is less than or equal to max_dist
            if distance <= max_dist:
                result.append(sorted_points[i])
            else:
                # Stop iteration if the distance is more than max_dist
                result.append(sorted_points[i])
                break

        return result


    def parse_str_board(self,board_string):
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
    
    def diff_boards(self,board1, board2, color, look_for_smaller=True):
        # Iterate through each position in both boards
        positions = []
        for i in range(len(board1)):
            # Check if color matches the specified color
            if board1[i][0] == color:
                # Check if color is the same and number of checkers in board1 is smaller than in board2
                if board1[i][0] == board2[i][0] or board2[i][0] == 0:
                    if look_for_smaller and board1[i][1] < board2[i][1]:
                        positions.append(i)
                    elif not look_for_smaller and board1[i][1] > board2[i][1]:
                        positions.append(i)
        return positions

    #calculate the movements that are required, in order for the actual board to be identical to expected board
    #it moves all wrong positions to correct positions. if there are wrong positions with no correct positions, it moves them to home
    def create_diff_movements(self,wrong_positions, correct_positions):
        movements = []

        # Iterate through the larger_positions list
        for i, larger_pos in enumerate(wrong_positions):
            # Get the corresponding smaller position if it exists
            smaller_pos = correct_positions[i] if i < len(correct_positions) else -1
            movements.append((larger_pos, smaller_pos))

        # Add tuples for remaining smaller positions
        for smaller_pos in correct_positions[len(wrong_positions):]:
            movements.append((-1, smaller_pos))

        return movements

    #takes the board, execute the movements and return the updated board, after the movements
    def update_board(self,board, movements):
        ret_val = list(board)  # Make a copy of the board

        # Iterate through the list of movements
        for movement in movements:
            decreased, increased = movement

            # Decrease count by 1 if the position matches decreased
            if decreased != -1:
                color_decreased, count_decreased = ret_val[decreased]
                if count_decreased > 0:
                    ret_val[decreased] = (color_decreased, count_decreased - 1)

                    # Add checker to empty column if the count is zero
                    if ret_val[increased][1] == 0:
                        ret_val[increased] = (color_decreased, 1)
                    else:
                        color_increased, count_increased = ret_val[increased]
                        ret_val[increased] = (color_increased, count_increased + 1)

        return ret_val


"""af = AuxFunctions()

expected_board = "0    b2 0 0 0 0 w5 0 w3 0 0  0   b5 w4 0   0  0  b3  0  b5 0  0   0 0  w2    0  "
actual_board = "0      b2 0 0 0 0 w5 0 w3 0 0  0   b5 w5 0   0  0  b3  0  b5 0  0   0 0  w1    0  "
#               "0     1  2 3 4 5 6  7 8  9 10 11  12 13 14  15 16 17 18  19 20 21 22 23 24   25  
board1 = af.parse_str_board(expected_board)
board2 = af.parse_str_board(actual_board)

before_movement = af.parse_str_board(actual_board)
after_movement = af.update_board(before_movement,[[1,2]])

expected_board = after_movement
actual_board = before_movement

board1,board2 = expected_board,actual_board

smaller_positions = af.diff_boards(board1, board2,True)
larger_positions = af.diff_boards(board1, board2,False)
tuples = af.create_diff_movements(smaller_positions,larger_positions)

print("Tuples:", tuples)"""