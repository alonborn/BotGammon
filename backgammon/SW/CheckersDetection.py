from dis import Positions
import cv2
import numpy as np
import copy
from AuxFunctions import AuxFunctions

af = AuxFunctions ()

class CheckersDetection:

	data_model = 0

	column_left_witdh = 0
	columns_right_width = 0
	board_right_start_pos = 0
	board_left_start_pos = 0
	board_left_size = 0
	board_position = 0
	screen = 0
	columns_positions = []
	bar_position = 0
	camera = 0
	
	HoughCircles_param1 = 265
	HoughCircles_param2 = 17
	
	circles_cache = []
	circles_gen = 0
	circles_gen_max = 20
	column_height_factor = 1.5
	ignore_rects = 0
	cur_x,cur_y = 0,0
	param1,param2 = 1,1

	def __init__ (self,camera):
		self.camera = camera
	def InitDetection(self,board_left_rect,board_right_rect,screen,data_model,ignore_rects):
		
		self.ignore_rects = ignore_rects


		self.screen = screen
		self.data_model = data_model

		self.UpdateColumnsPositions()

	def UpdateColumnsPositions(self):
		self.mid_size_y_right = int((self.camera.board_right_rect[1][1]-self.camera.board_right_rect[0][1])/2)
		self.mid_size_y_left = int((self.camera.board_left_rect[1][1]-self.camera.board_left_rect[0][1])/2)
		
		self.board_right_start_pos = self.camera.board_right_rect[0]
		self.board_left_start_pos = self.camera.board_left_rect[0]

		self.position_left_width = int((self.camera.board_left_rect[1][0] -self.camera.board_left_rect[0][0] ) / 6)
		self.position_right_width = int((self.camera.board_right_rect[1][0] -self.camera.board_right_rect[0][0] ) / 6)

		self.bar_position = ((self.camera.board_left_rect[1][0],self.camera.board_left_rect[0][1]),(self.camera.board_right_rect[0][0],self.camera.board_left_rect[1][1]))
		self.column_left_witdh = (self.camera.board_left_rect[1][0] - self.camera.board_left_rect[0][0]) / 6
		self.column_right_witdh = (self.camera.board_right_rect[1][0] - self.camera.board_right_rect[0][0]) / 6

	def GetValidCircles (self,circles,image):
		outside_rect_circles = []  # List to store circles outside the rectangle
		
		if circles is not None:
			#circles = np.uint16(np.around(circles))

			# Define the coordinates of the rectangle (x, y, width, height)

			for circle in circles[0, :]:
				x, y = circle[0], circle[1]

				circle_is_valid = True

				if circle_is_valid:
					point = (x,y)
					if self.IsInsideRectangle(point,self.camera.board_left_rect) or \
						self.IsInsideRectangle(point,self.camera.board_right_rect) or \
						self.IsInsideRectangle(point,self.bar_position):
						outside_rect_circles.append([circle[0],circle[1],circle[2]])

		return outside_rect_circles


	def CalcCirclesFromCache(self):
		# Use list comprehension to calculate the average of each internal list
		averages = [np.mean([point[0] for point in internal_list], axis=0) for internal_list in self.circles_cache]

		
		return copy.deepcopy(averages)


	def UpdateCirclesCache(self, new_points, d=10):
		if new_points == []:
			return
		if not self.circles_cache:
			self.circles_cache.append([[new_points[0], self.circles_gen]])

		updated_indices = set()

		for new_point in new_points:
			# Calculate the average of each internal list
			averages = [np.mean([point[0] for point in internal_list], axis=0) for internal_list in self.circles_cache]

			# Calculate the distances between the averages and the new point
			distances = [np.linalg.norm(np.array(avg) - np.array(new_point)) for avg in averages]

			# Check if any distance is less than 'd'
			if any(distance < d for distance in distances):
				for i, internal_list in enumerate(self.circles_cache):
					if distances[i] < d:
						# Check if any point in the internal list has the same generation as 'gen'
						has_same_gen = any(point[1] == self.circles_gen for point in internal_list)

						if has_same_gen:
							self.circles_cache[i] = [[new_point, self.circles_gen] if point[1] == self.circles_gen else point for point in internal_list]
							updated_indices.add(i)
						else:
							# Add the new point and generation number to the internal list
							self.circles_cache[i].append([new_point, self.circles_gen])
							updated_indices.add(i)
						break
			else:
				# Create a new internal list with the new point and generation number
				self.circles_cache.append([[new_point, self.circles_gen]])
				updated_indices.add(len(self.circles_cache) - 1)

		# Remove internal lists that were not updated
		self.circles_cache = [self.circles_cache[i] for i in updated_indices]

		self.circles_gen += 1

		if self.circles_gen == self.circles_gen_max:
			self.circles_gen = 0

	

	def DetectCheckers(self,image):
		circles = self.ExtractCirclesFromImage(image)
		self.UpdateCirclesCache(circles)
		circles = self.CalcCirclesFromCache()
		#if circles != None:
		circles	= np.uint16(np.around(circles))
		return circles

	def ExtractCirclesFromImage(self, image):
		gray_img = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
			#cv2.imshow("greyimage",gray_img)
		#img	= cv2.medianBlur(gray_img,5)
		img = gray_img
			#cv2.imshow("blur",img)

		circles	= cv2.HoughCircles(img,cv2.HOUGH_GRADIENT,0.8,45,param1=self.HoughCircles_param1,param2=self.HoughCircles_param2,minRadius=23,maxRadius=27)
		circles = self.GetValidCircles(circles,image)
		return circles

	def ArrangeColumns(self):
		self.columns_positions = []

		for i in range(6):
			pos = ((self.camera.board_right_rect[1][0] - (i+1)*self.position_right_width),self.board_right_start_pos[1])
			pos = (int(pos[0]),int(pos[1]))
			self.columns_positions.append(pos)
		for i in range(6):
			point = ((self.camera.board_left_rect[1][0] - (i+1)*self.position_left_width),self.board_left_start_pos[1])
			point  = (int(point [0]),int(point [1]))
			self.columns_positions.append (point)
		for i in range(5,-1,-1):
			point = ((self.camera.board_left_rect[1][0] - (i+1)*self.position_left_width),(self.mid_size_y_left/2.)+self.board_left_start_pos[1])
			point  = (int(point [0]),int(point [1]))
			self.columns_positions.append (point)	
		for i in range(5,-1,-1):
			point = ((self.camera.board_right_rect[1][0] - (i+1)*self.position_right_width),(self.mid_size_y_right/2.) +self.board_right_start_pos[1])
			point  = (int(point [0]),int(point [1]))
			self.columns_positions.append (point)
		
	def DrawColumns(self,image):
		color = (255, 0, 0)
		column_num = 0
		for pos in self.columns_positions:
			start_point = pos
			if 0 <= column_num < 6 or 18 <= column_num < 25:
				column_width = self.column_right_witdh
				column_height = self.mid_size_y_right
				color = (255, 255, 255)
			else:
				column_width = self.column_left_witdh
				column_height = self.mid_size_y_left
				color = (0, 0, 0)
			column_width= int(column_width)
			column_height= int(column_height)
			column_height*=self.column_height_factor
			end_point = (int(pos[0])+ column_width,int(pos[1]) + int(column_height))
			cv2.rectangle(image,start_point,end_point,color,2)
			column_num = column_num + 1
		cv2.rectangle(image,self.bar_position[0],self.bar_position[1],color,2)
		
	
	def IsInsideRectangle(self,point, rectangle):
		x, y = point
		(x1, y1), (x2, y2) = rectangle
		
		if x1 < x < x2 and y1 < y < y2:
			return True
		else:
			return False

	def DrawBoard(self,image,checkers):
		#board = ((self.board_position[0][0],self.board_position[0][1]),(self.board_position[0][0] + width,self.board_position[0][1]+height))

		#for	i in checkers[0,:]:
		for	i in checkers:
			#if i[0] >= board[0][0] and i[0] <= board[1][0] and i[1] >= board[0][1] and i[1] <= board[1][1]:
			point = (i[0],i[1])
					#	draw	the	outer	circle
			cv2.circle(image,(i[0],i[1]),i[2],(0,255,0),2)
					#	draw	the	center	of	the	circle
					#cv2.circle(image,(i[0],i[1]),2,(0,0,255),3)
		
		self.DrawColumns(image)
		#image = cv2.flip(image,0)

		cur_pos = str(self.cur_x) + "," + str(self.cur_y)
		cv2.putText(image, cur_pos, (900,700),cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)

		self.screen.board_image = image
		#self.screen.ShowWindows()		

	def IsWithinIgnoreRects(self,pos):
		(x,y) = pos
		for rect in self.ignore_rects:
			rect_x, rect_y, rect_width, rect_height = rect[0][0], rect[0][1], rect[1][0]-rect[0][0], rect[1][1]-rect[0][1]
			
			if ((rect_x <= x <= (rect_x + rect_width) and rect_y <= y <= (rect_y + rect_height))):	
				return  True
		return False



	def IsCheckerColorValid(self,image,pos):
		checker_rad = int(self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[0]) - 4

		if self.IsWithinIgnoreRects(pos):
			num_black = af.mean_max_values_around_point(image, pos, checker_rad)

			if num_black < 80 or num_black > 850:
				return True
			return False
		else:
			return True
			
	def detect_black_white(self,gsimage,image,pos):
		bgr_values = image[pos[1], pos[0]]

		#check if the checker is black or white
		pixel_value = gsimage[pos[1], pos[0]]
		rect = gsimage[pos[1]-5:pos[1]+5, pos[0]-5:pos[0]+5]
		pixel_value = rect.mean()
		std_pixel_value = rect.std()
		
		if all(x <100 for x in bgr_values):
			return 'b'
		
		if bgr_values[0] >120 and bgr_values[1] > 110 and bgr_values[2] >100:
			return 'w'
		
		return None
	
		"""if bgr_values[2] > 70:
		#if pixel_value > 40 :
			return "w"
		return "b"""

	def GetBarCheckers(self,checkers,gsimage,image):
		black_bar,white_bar =0,0
		#self.data_model.bar_checkers = [[],[]]
		white_checkers = []
		black_checkers = []

		for	i in checkers:
			if i[0] >= self.bar_position[0][0] and i[0] <= self.bar_position[1][0] and i[1] >= self.bar_position[0][1] and i[1] <= self.bar_position[1][1]:
				color = self.detect_black_white(gsimage,image ,(i[0],i[1]))
				if (color == "w"):
					white_bar = white_bar + 1
					white_checkers.append((i[0],i[1]))
				elif color == 'b':
					black_bar = black_bar + 1
					black_checkers.append((i[0],i[1]))
		return black_checkers,white_checkers

	def GetColumnDimensions(self,column):
		if 0 <= column < 6 or 18 <= column < 25:
			column_width = self.column_right_witdh
			column_height = self.mid_size_y_right*self.column_height_factor
		else:
			column_width = self.column_left_witdh
			column_height = self.mid_size_y_left * self.column_height_factor
		return column_width,column_height
	
	def GetColumnColor(self,tmp_checkers,column_num):
		
		result = None
		if column_num >11:
			result = max(tmp_checkers, key=lambda x: x[0][1])[1]
		else:
			result = min(tmp_checkers, key=lambda x: x[0][1])[1]
		return result 	

	def GetColumnCheckers(self,checkers,target_color):
		return [point for point, color in checkers if color == target_color]
	
	def IsColumnStartsCorrectly(self,tmp_checkers,column_num,min_dist):
		extreme_y = 0

		if 0<=column_num<6:
			extreme_y = self.camera.board_right_rect[0][1]
		if 6<=column_num<12:
			extreme_y = self.camera.board_left_rect[0][1]
		if 12<=column_num<18:
			extreme_y = self.camera.board_left_rect[1][1]
		if 18<=column_num<24:
			extreme_y = self.camera.board_right_rect[1][1]

		sorted_checkers = []

		if 0<=column_num<12:
			sorted_checkers = sorted(tmp_checkers, key=lambda x: x[0][1])
		else:
			sorted_checkers = sorted(tmp_checkers, key=lambda x: x[0][1],reverse=True)

		if abs(sorted_checkers[0][0][1] - extreme_y) > min_dist:
			return False
		return True

	#calculates how many checkers in each columns
	#the data goes to a chache in the data_model, later on used when reducing the noise in the screen.
	def calc_checkers_on_board(self,image,checkers):
		pos_num = 1
		board = ""
		
		gsimage = gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		black_bar,white_bar = self.GetBarCheckers(checkers,gsimage,image)

		self.data_model.bar_checkers_black_cahce[len(black_bar)] = black_bar
		self.data_model.bar_checkers_white_cahce[len(white_bar)] = white_bar

		board = "b" + str(len(black_bar)) + " "
		current_checkers = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]

		column_num = 0
		
		#calculate how many checkers are in the rectagle
		for pos in self.columns_positions:
			column_width,column_height = self.GetColumnDimensions(column_num)
			color = ""
			in_rect = 0
			#for	i in checkers[0,:]:
			tmp_checkers = []
			for	i in checkers:
				if i[0] > pos[0] and i[0] <= pos[0] + column_width and i[1] >= pos[1] and i[1] <= pos[1] + int(column_height):
					if self.IsCheckerColorValid(gsimage,(i[0],i[1])):
						tmp_color = self.detect_black_white(gsimage,image ,(i[0],i[1]))				
						if tmp_color in ['b','w']:
							#in_rect += 1
							#current_checkers[column_num].append((i[0],i[1]))
							#update last checker
							#if color == "":
							#	color = tmp_color
							tmp_checkers.append(((i[0],i[1]),tmp_color))
			if tmp_checkers != []:
				start_from_top = True if column_num > 11 else False
				if self.IsColumnStartsCorrectly(tmp_checkers,column_num,50):
					color = self.GetColumnColor(tmp_checkers,column_num)
					tmp_checkers = af.get_points_until_distance(tmp_checkers,80,start_from_top)
					current_checkers[column_num].extend(self.GetColumnCheckers(tmp_checkers,color))
					in_rect = len(current_checkers[column_num])
			board += color + str(in_rect) + " "
			column_num += 1
		#self.data_model.last_checker = [None if second_item == 10000 else (first_item, second_item) for first_item, second_item in self.data_model.last_checker]		
		board += "w" + str(len(white_bar)) + " "

		#update_all_checkers_cache, according to the last image:

		for i in range(24):
			self.data_model.all_checkers_cache[i][len(current_checkers[i])] = current_checkers[i].copy()
		return board





	#assumption - there are at least eight checkers on the board, in each corner. Adjust board rectangles according to them
	def AdjustRectangles(self):
		all_checkers = [item for sublist in self.data_model.all_checkers for item in sublist]

		x_sorted = sorted(all_checkers, key=lambda x: x[0])
		if len(x_sorted) < 8:
			print ("*************************Cannot set rectangles!!!!! -*****************************")
			return
		
		mid_point = x_sorted[0][0] + (x_sorted[-1][0] - x_sorted[0][0])/2

		left_rect_points = [item for item in x_sorted if item[0] < mid_point]
		right_rect_points = [item for item in x_sorted if item[0] >= mid_point]

		#left_rect_points = x_sorted[:4]
		#right_rect_points = x_sorted[4:]

		left_min_x = sorted(left_rect_points, key=lambda x: x[0])[0][0]
		left_min_y = sorted(left_rect_points, key=lambda y: y[1])[0][1]

		left_max_x = sorted(left_rect_points, key=lambda x: x[0], reverse=True)[0][0]
		left_max_y = sorted(left_rect_points, key=lambda y: y[1], reverse=True)[0][1]


		right_min_x = sorted(right_rect_points, key=lambda x: x[0])[0][0]
		right_min_y = sorted(right_rect_points, key=lambda y: y[1])[0][1]

		right_max_x = sorted(right_rect_points, key=lambda x: x[0], reverse=True)[0][0]
		right_max_y = sorted(right_rect_points, key=lambda y: y[1], reverse=True)[0][1]

		checker_rad_x = int(self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[0])
		checker_rad_y = int(self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[1])

		self.camera.board_left_rect = [[int(left_min_x-checker_rad_x),int(left_min_y-checker_rad_y)],[int(left_max_x+checker_rad_x),int(left_max_y+checker_rad_y)]]	
		self.camera.board_right_rect = [[int(right_min_x-checker_rad_x),int(right_min_y-checker_rad_y)],[int(right_max_x+checker_rad_x-10),int(right_max_y+checker_rad_y)]]	#-10 because the width of the columns on the upper side are too large

		self.UpdateColumnsPositions() 
		self.camera.SaveToFile()
		
