from rest_framework import serializers
from .models import Rooms, Meeting
from datetime import timedelta, datetime


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rooms
        fields = '__all__'

class MeetingSerializer(serializers.ModelSerializer):
    room_details = RoomSerializer(source='room', read_only=True)

    class Meta:
        model = Meeting
        fields = '__all__'

    def validate(self, data):
        # Extract required fields from the validated data
        room = data.get('room')
        meeting_date = data.get('Date')
        start_time = data.get('start_time')
        duration = data.get('Duration')

        # Calculate the end time of the meeting
        # end_time = (timedelta(seconds=start_time.hour * 3600 + start_time.minute * 60) + duration).seconds
        # end_time = timedelta(seconds=end_time)

        # Combine meeting_date and start_time to create a datetime object
        start_datetime = datetime.combine(meeting_date, start_time)
        end_datetime = start_datetime + duration

        # Query to check for overlapping meetings
        overlapping_meetings = Meeting.objects.filter(
            room=room,
            Date=meeting_date,
        ).exclude(
            id=self.instance.id if self.instance else None  # Exclude self if updating
        ).filter(
            start_time__lt=end_datetime.time(),  # Starts before this meeting ends
            start_time__gte=start_datetime.time()  # Ends after this meeting starts
            #start_time__lt=(start_time + duration),  # Starts before this meeting ends
            #start_time__gte=end_time
        )

        if overlapping_meetings.exists():
            raise serializers.ValidationError("This room is already booked for the selected time slot.")

        return data
