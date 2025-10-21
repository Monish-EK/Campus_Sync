import streamlit as st
import os
import calendar
from datetime import datetime
import json
import cv2
import easyocr
import re

DATA_FILE = "schedule.json"

def show():
    st.title("📅 Timetable Scheduler")
    
    # Initialize session states if not already done
    if "data" not in st.session_state:
        DATA_FILE = "schedule.json"
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                st.session_state["data"] = json.load(f)
        else:
            st.session_state["data"] = {"events": {}, "assignments": {}, "finalized_dates": []}

    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = None
    
    # Function to save schedule data
    def save_data(data):
        with open("schedule.json", "w") as f:
            json.dump(data, f, indent=4)
    
    # Helper functions for the scheduler
    def extract_text_from_image(image_path):
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            reader = easyocr.Reader(['en'])
            results = reader.readtext(gray)
            extracted_text = "\n".join([res[1] for res in results])
            return extracted_text
        except Exception as e:
            st.error(f"Error in OCR: {e}")
            return "Error in text extraction"

    def detect_schedule(text):
        schedule_pattern = r'([A-Za-z\s]+)\s(\d{1,2}:\d{2}\s?(?:AM|PM)?)\s(\d{1,2}:\d{2}\s?(?:AM|PM)?)'
        matches = re.findall(schedule_pattern, text)
        events = []
        conflicts = []

        for match in matches:
            subject, start_time, end_time = match
            subject = subject.strip()

            try:
                start_dt = datetime.strptime(start_time, "%I:%M %p")
                end_dt = datetime.strptime(end_time, "%I:%M %p")

                for e in events:
                    existing_start = datetime.strptime(e["start_time"], "%I:%M %p")
                    existing_end = datetime.strptime(e["end_time"], "%I:%M %p")

                    if (start_dt < existing_end and end_dt > existing_start):
                        conflicts.append(f"⚠ Conflict: {subject} overlaps with {e['name']}")

                events.append({"name": subject, "start_time": start_time, "end_time": end_time})
            except ValueError:
                pass

        return events, conflicts

    def add_event(date, name, start_time, end_time):
        if date not in st.session_state["data"]["events"]:
            st.session_state["data"]["events"][date] = []

        st.session_state["data"]["events"][date].append({
            "name": name, "start_time": start_time, "end_time": end_time
        })
        save_data(st.session_state["data"])

    def delete_event(date, event_name):
        if date in st.session_state["data"]["events"]:
            st.session_state["data"]["events"][date] = [
                e for e in st.session_state["data"]["events"][date] if e["name"] != event_name
            ]
            save_data(st.session_state["data"])
            st.success(f"🗑 Deleted event: {event_name}")
            st.rerun()

    def add_assignment(date, name, due_date, assigned_staff="N/A"):
        if date not in st.session_state["data"]["assignments"]:
            st.session_state["data"]["assignments"][date] = []

        st.session_state["data"]["assignments"][date].append({
            "name": name,
            "due_date": due_date,
            "assigned_staff": assigned_staff if assigned_staff else "N/A"
        })
        save_data(st.session_state["data"])


    def delete_assignment(date, assignment_name):
        if date in st.session_state["data"]["assignments"]:
            st.session_state["data"]["assignments"][date] = [
                a for a in st.session_state["data"]["assignments"][date] if a["name"] != assignment_name
            ]
            save_data(st.session_state["data"])
            st.success(f"🗑 Deleted assignment: {assignment_name}")
            st.rerun()

    def finalize_timetable(date):
        if date not in st.session_state["data"]["finalized_dates"]:
            st.session_state["data"]["finalized_dates"].append(date)
            save_data(st.session_state["data"])
            st.success("✅ Timetable finalized!")
            st.rerun()

    def delete_schedule(date):
        if date in st.session_state["data"]["events"]:
            del st.session_state["data"]["events"][date]
        if date in st.session_state["data"]["assignments"]:
            del st.session_state["data"]["assignments"][date]
        if date in st.session_state["data"]["finalized_dates"]:
            st.session_state["data"]["finalized_dates"].remove(date)
        save_data(st.session_state["data"])
        st.success(f"🗑 Deleted full schedule for {date}")
        st.rerun()

    def calendar_view(year, month):
        st.write(f"## {calendar.month_name[month]} {year}")
        cols = st.columns(7)
        for col, day in zip(cols, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            col.markdown(f"**{day}**")

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)
        for week in month_days:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    button_label = f"{day} ✅" if date_str in st.session_state["data"]["finalized_dates"] else f"{day} +"
                    if cols[i].button(button_label, key=date_str):
                        st.session_state["selected_date"] = date_str
                        st.rerun()

    def event_view(selected_date):
        st.write(f"## Events and Assignments for {selected_date}")
        
        # Display events
        events = st.session_state["data"]["events"].get(selected_date, [])
        st.subheader("📖 **Timetable**")
        if events:
            for event in sorted(events, key=lambda e: datetime.strptime(e["start_time"], "%I:%M %p") if ":" in e["start_time"] else datetime.now()):
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{event['name']}** | ⏰ {event['start_time']} - {event['end_time']}")
                if col2.button("🗑 Delete Event", key=f"del_event_{event['name']}"):
                    delete_event(selected_date, event["name"])
        else:
            st.warning("No events scheduled for this day.")

        # Display assignments
        assignments = st.session_state["data"]["assignments"].get(selected_date, [])
        st.subheader("📚 **Assignments**")
        if assignments:
            for assignment in assignments:
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{assignment['name']}** | 📅 Due: {assignment['due_date']} | 🧑‍🏫 Assigned to: {assignment['assigned_staff']}")
                if col2.button("🗑 Delete Assignment", key=f"del_assignment_{assignment['name']}"):
                    delete_assignment(selected_date, assignment["name"])
        else:
            st.warning("No assignments for this day.")

        # Add event
        if selected_date in st.session_state["data"]["finalized_dates"]:
            st.success("✅ Timetable finalized.")
            if st.button("🗑 Delete Full Schedule"):
                delete_schedule(selected_date)
        else:
            st.subheader("➕ Add Event")
            name = st.text_input("Event Name")
            start_time = st.text_input("Start Time (e.g., 10:00 AM)")
            end_time = st.text_input("End Time (e.g., 12:00 PM)")
            if st.button("Add Event"):
                add_event(selected_date, name, start_time, end_time)
                st.success("✅ Event added successfully!")
                st.rerun()

            # Add assignment
            st.subheader("➕ Add Assignment")
            assignment_name = st.text_input("Assignment Name")
            due_date = st.text_input("Due Date (e.g., 2025-03-10)")
            assigned_staff = st.text_input("Assigned Staff")
            if st.button("Add Assignment"):
                add_assignment(selected_date, assignment_name, due_date, assigned_staff)
                st.success("✅ Assignment added successfully!")
                st.rerun()

            # Upload timetable image for OCR
            uploaded_file = st.file_uploader("Upload Timetable Image", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                with open("temp.jpg", "wb") as f:
                    f.write(uploaded_file.read())

                extracted_text = extract_text_from_image("temp.jpg")
                schedule, conflicts = detect_schedule(extracted_text)

                st.subheader("🕒 Organized Schedule")
                if schedule:
                    for event in schedule:
                        st.write(f"**{event['name']}** | ⏰ {event['start_time']} - {event['end_time']}")
                else:
                    st.write("No schedule detected.")

                if conflicts:
                    st.subheader("⚠ Conflict Alerts")
                    for conflict in conflicts:
                        st.error(conflict)
                else:
                    st.success("✅ No conflicts detected!")

                if not conflicts and st.button("Finalize Timetable"):
                    finalize_timetable(selected_date)

        if st.button("← Back to Calendar"):
            st.session_state.pop("selected_date", None)
            st.rerun()

    # Display the calendar or event view based on state
    today = datetime.today()
    
    if st.session_state["selected_date"]:
        event_view(st.session_state["selected_date"])
    else:
        calendar_view(today.year, today.month)