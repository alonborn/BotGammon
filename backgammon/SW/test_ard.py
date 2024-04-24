def parallel_lines(point1, point2, distance):
    x1, y1 = point1
    x2, y2 = point2

    # Calculate the slope (m)
    if x1 == x2:
        # Vertical line, return x = constant
        return f'x = {x1}', f'x = {x1 - distance}', f'x = {x1 + distance}'
    else:
        m = (y2 - y1) / (x2 - x1)

    # Calculate the y-intercept (b)
    b = y1 - m * x1

    # Calculate the y-intercepts for parallel lines
    b_left = b + distance
    b_right = b - distance

    return m,b_left,b_right

# Example usage:
"""point1 = (1, 2)
point2 = (3, 4)
result = line_between_points(point1, point2)
print(result)"""