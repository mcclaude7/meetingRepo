from datetime import datetime
from rest_framework import viewsets
from .models import Rooms, Meeting
from .serializers import RoomSerializer, MeetingSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import render
from rest_framework import status

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Rooms.objects.all()
    serializer_class = RoomSerializer

class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.select_related('room').all()
    serializer_class = MeetingSerializer

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Custom action to retrieve upcoming meetings.
        """
        upcoming_meetings = self.queryset.filter(Date__gte=datetime.date.today())
        serializer = self.get_serializer(upcoming_meetings, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        room_id = request.data.get("room")
        start_time = request.data.get("start_time")
        date = request.data.get("Date")

        # Convert start_time to a datetime object (assuming it's in HH:MM:SS format)
        #start_time = datetime.strptime(start_time, "%H:%M:%S").time()

        # Check if time format is HH:MM (without seconds) and append ':00' if needed
        if len(start_time) == 5:  # If the time string is in 'HH:MM' format
            start_time = start_time + ":00"  # Add ':00' to represent seconds

        try:
            # Convert start_time to a datetime object (assuming it's in HH:MM:SS format)
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()
        except ValueError:
            return Response({"error": "Invalid time format. Use HH:MM:SS."}, status=status.HTTP_400_BAD_REQUEST)


        # Check if the room is already booked at the given date and time
        existing_meeting = Meeting.objects.filter(room_id=room_id, Date=date, start_time=start_time).first()

        if existing_meeting:
            # Find the next available time for the room
            next_available_meeting = Meeting.objects.filter(room_id=room_id, Date=date, start_time__gt=start_time).order_by("start_time").first()
            if next_available_meeting:
                next_available_time = next_available_meeting.start_time
            else:
                next_available_time = "No further bookings on this day"
            
            message = {
                "error": "This room is already booked for this time.",
                "next_available": next_available_time
            }
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        
        # If the room is available, proceed with creating the meeting
        return super().create(request, *args, **kwargs)

def application_interface(request):
    rooms = Rooms.objects.all()
    meetings = Meeting.objects.select_related('room').all()
    return render(request, 'interface.html', {'rooms': rooms, 'meetings': meetings})
