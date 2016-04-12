from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from app_calendar.models import UserEvent
from app_account_management.models import UserExtended
from .views import *

class FreeBlocksTestCase(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.user1 = User.objects.create(username="user1", password="password")
		UserExtended.objects.create(authenticated_user = self.user1, wakeup_time = "8:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")
		
		self.user2 = User.objects.create(username="user2", password="password")
		UserExtended.objects.create(authenticated_user = self.user2, wakeup_time = "11:00", 
									sleepy_time = "3:00", time_zone = "America/Phoenix",
									min_task_time="0", travel_time = "0")
		
		self.user3 = User.objects.create(username="user3", password="password")
		UserExtended.objects.create(authenticated_user = self.user3, wakeup_time = "8:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")

		#Change start and end time according to current day
		UserEvent.objects.create(authenticated_user = self.user3, start_time = "2016-04-11T7:00:00Z", end_time = "2016-04-11T9:00:00Z")
		
		self.user4 = User.objects.create(username="user4", password="password")
		UserExtended.objects.create(authenticated_user = self.user4, wakeup_time = "8:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")

		UserEvent.objects.create(authenticated_user = self.user4, start_time = "2016-04-11T7:00:00Z", end_time = "2016-04-11T9:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user4, start_time = "2016-04-11T6:00:00Z", end_time = "2016-04-11T10:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user4, start_time = "2016-04-11T8:00:00Z", end_time = "2016-04-11T11:00:00Z")

	def test_all_week_free1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user1

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T8:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))

		# expected_list = [	('2016-02-01T8:00:00Z', '2016-02-01T20:00:00Z'), 
		# 					('2016-02-02T8:00:00Z', '2016-02-02T20:00:00Z'), 
		# 					('2016-02-03T8:00:00Z', '2016-02-03T20:00:00Z'), 
		# 					('2016-02-04T8:00:00Z', '2016-02-04T20:00:00Z'), 
		# 					('2016-02-05T8:00:00Z', '2016-02-05T20:00:00Z'), 
		# 					('2016-02-06T8:00:00Z', '2016-02-06T20:00:00Z'), 
		# 					('2016-02-07T8:00:00Z', '2016-02-07T20:00:00Z')]
		self.assertEqual(expected_list, free_time)

	def test_all_week_free2(self):
		request = self.factory.get('/archicalc')
		request.user = self.user2

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []
		
		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start_day = day[0:10] + "T00:00:00Z"
			end_day = day[0:10] + "T23:59:59Z"
			start = day[0:10] + "T11:00:00Z"
			end = day[0:10] + "T3:00:00Z"
			expected_list.append((start_day, end))
			expected_list.append((start, end_day))

		# expected_list = [	('2016-02-01T00:00:00Z', '2016-02-01T3:00:00Z'),
		# 					('2016-02-01T11:00:00Z', '2016-02-01T23:59:59Z'), 
		# 					('2016-02-02T00:00:00Z', '2016-02-02T3:00:00Z'),
		# 					('2016-02-02T11:00:00Z', '2016-02-02T23:59:59Z'), 
		# 					('2016-02-03T00:00:00Z', '2016-02-03T3:00:00Z'),
		# 					('2016-02-03T11:00:00Z', '2016-02-03T23:59:59Z'), 
		# 					('2016-02-04T00:00:00Z', '2016-02-04T3:00:00Z'),
		# 					('2016-02-04T11:00:00Z', '2016-02-04T23:59:59Z'), 
		# 					('2016-02-05T00:00:00Z', '2016-02-05T3:00:00Z'),
		# 					('2016-02-05T11:00:00Z', '2016-02-05T23:59:59Z'), 
		# 					('2016-02-06T00:00:00Z', '2016-02-06T3:00:00Z'),
		# 					('2016-02-06T11:00:00Z', '2016-02-06T23:59:59Z'), 
		# 					('2016-02-07T00:00:00Z', '2016-02-07T3:00:00Z'),
		# 					('2016-02-07T11:00:00Z', '2016-02-07T23:59:59Z'),]
		self.assertEqual(expected_list, free_time)

	def test_overlap_wakeup1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user3

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T8:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))
		start = days_in_current_week[0][0:10] + "T09:00:00Z"
		end = days_in_current_week[0][0:10] + "T20:00:00Z"
		expected_list[0] = (start, end)

		# expected_list = [	('2016-04-11T09:00:00Z', '2016-04-11T20:00:00Z'), 
		# 					('2016-04-12T8:00:00Z', '2016-04-12T20:00:00Z'), 
		# 					('2016-04-13T8:00:00Z', '2016-04-13T20:00:00Z'), 
		# 					('2016-04-14T8:00:00Z', '2016-04-14T20:00:00Z'), 
		# 					('2016-04-15T8:00:00Z', '2016-04-15T20:00:00Z'), 
		# 					('2016-04-16T8:00:00Z', '2016-04-16T20:00:00Z'), 
		# 					('2016-04-17T8:00:00Z', '2016-04-17T20:00:00Z')]
		print expected_list
		print free_time

		self.assertEqual(expected_list, free_time)

	def test_overlap_wakeup_cluster1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user4

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T8:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))
		start = days_in_current_week[0][0:10] + "T11:00:00Z"
		end = days_in_current_week[0][0:10] + "T20:00:00Z"
		expected_list[0] = (start, end)

		# expected_list = [	('2016-04-11T11:00:00Z', '2016-04-11T20:00:00Z'), 
		# 					('2016-04-12T8:00:00Z', '2016-04-12T20:00:00Z'), 
		# 					('2016-04-13T8:00:00Z', '2016-04-13T20:00:00Z'), 
		# 					('2016-04-14T8:00:00Z', '2016-04-14T20:00:00Z'), 
		# 					('2016-04-15T8:00:00Z', '2016-04-15T20:00:00Z'), 
		# 					('2016-04-16T8:00:00Z', '2016-04-16T20:00:00Z'), 
		# 					('2016-04-17T8:00:00Z', '2016-04-17T20:00:00Z')]
		# print expected_list
		# print free_time
		self.assertEqual(expected_list, free_time)