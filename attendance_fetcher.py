from zk import ZK
import datetime
import pandas as pd
import logging
import socket
import ipaddress
from cryptography.fernet import Fernet

# Updated predefined devices
predefined_devices = {
    "1": {"name": "MainWarehouse", "ip": "10.10.10.202"},
    "2": {"name": "HeadOffice", "ip": "10.10.10.201"},
    "3": {"name": "MerghanyBranch", "ip": "196.202.26.217"},
    "4": {"name": "MaadiBranch", "ip": "196.202.19.227"},
    "5": {"name": "KhufuBranch", "ip": "192.168.1.201"},
    "6": {"name": "The-StripBranch", "ip": "196.221.149.209"},
    "7": {"name": "OraBranch", "ip": "192.168.1.201"},
}

def connect_device(ip):
    zk = ZK(ip, port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)
    try:
        conn = zk.connect()
        conn.disable_device()
        return conn
    except Exception as e:
        print(f"Connection to {ip} failed: {e}")
        return None

def get_period():
    today = datetime.datetime.now()
    first_day_this_month = today.replace(day=1)
    last_month = first_day_this_month - datetime.timedelta(days=1)
    start_date = last_month.replace(day=25, hour=0, minute=0, second=0)
    end_date = today.replace(hour=23, minute=59, second=59)
    return start_date, end_date

def fetch_attendance(ip, name):
    start_date, end_date = get_period()
    conn = connect_device(ip)
    if conn:
        try:
            logs = conn.get_attendance()
            filtered_logs = [log for log in logs if start_date <= log.timestamp <= end_date]
            if filtered_logs:
                filename = f"{name}_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
                with open(filename, "w") as file:
                    file.write("UserID,DateTime,Status,InOutMode\n")
                    for log in filtered_logs:
                        file.write(f"{log.user_id},{log.timestamp},{log.status},{log.punch}\n")
                print(f"Saved {len(filtered_logs)} logs to {filename}")
            else:
                print(f"No logs found for {name} in specified period.")
        except Exception as e:
            print(f"Error processing device {name}: {e}")
        finally:
            conn.enable_device()
            conn.disconnect()
        device_operations_menu(ip, name)
    else:
        print(f"Failed to connect to device: {name}")

def fetch_attendance_from_all_devices():
    for key, device in predefined_devices.items():
        print(f"\nConnecting to device: {device['name']} ({device['ip']})")
        fetch_attendance(device["ip"], device["name"])

def device_operations_menu(ip, name):
    conn = connect_device(ip)
    if not conn:
        print("Unable to connect to device for operations menu.")
        return
    while True:
        print(f"\nDevice Menu - {name}")
        print("1. Get Attendance Data")
        print("2. Set Date/Time")
        print("3. Restart Device")
        print("4. Change Device")
        print("5. Backup Device Data")
        print("6. Add New User")
        print("7. Delete Logs")
        print("8. Get Device Info")
        print("9. Real-Time Monitoring")
        print("10. Schedule Data Fetch")
        print("11. Go to Main Menu")
        choice = input("Select option: ")

        if choice == "1":
            fetch_attendance(ip, name)
        elif choice == "2":
            now = datetime.datetime.now()
            conn.set_time(now)
            print(f"Device time updated to: {now}")
        elif choice == "3":
            conn.restart()
            print("Device restarting...")
        elif choice == "4":
            break
        elif choice == "5":
            users = conn.get_users()
            logs = conn.get_attendance()
            backup_filename = f"{name}_backup_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
            backup_data = {
                "users": [{"user_id": u.user_id, "name": u.name} for u in users],
                "logs": [{"user_id": l.user_id, "timestamp": str(l.timestamp), "status": l.status, "punch": l.punch} for l in logs]
            }
            with open(backup_filename, "w") as file:
                import json
                json.dump(backup_data, file, indent=4)
            print(f"Backup saved to {backup_filename}")
        elif choice == "6":
            user_id = input("Enter User ID: ")
            name_input = input("Enter User Name: ")
            privilege = int(input("Enter Privilege (0 for User, 1 for Admin): "))
            conn.set_user(user_id=user_id, name=name_input, privilege=privilege)
            print("User added successfully.")
        elif choice == "7":
            start_date, end_date = get_period()
            logs = conn.get_attendance()
            to_delete = [log for log in logs if start_date <= log.timestamp <= end_date]
            for log in to_delete:
                conn.delete_attendance(log)
            print(f"Deleted {len(to_delete)} logs from the device.")
        elif choice == "8":
            info = {
    "device_name": conn.get_device_name(),
    "serial_number": conn.get_serialnumber(),
    "firmware_version": conn.get_firmware_version()
}
            print("\nDevice Info:")
            print(f"Device Name: {info.device_name}")
            print(f"Serial Number: {info.serial_number}")
            print(f"Firmware Version: {info.firmware_version}")
        elif choice == "9":
            print("Real-time monitoring started. Press Ctrl+C to stop.")
            try:
                while True:
                    logs = conn.get_attendance()
                    for log in logs:
                        print(f"UserID: {log.user_id}, DateTime: {log.timestamp}, Status: {log.status}, Mode: {log.punch}")
            except KeyboardInterrupt:
                print("Monitoring stopped.")
        elif choice == "10":
            import schedule
            import time as t
            def job():
                fetch_attendance(ip, name)
            schedule.every().day.at("09:00").do(job)
            print("Scheduler started. Press Ctrl+C to stop.")
            try:
                while True:
                    schedule.run_pending()
                    t.sleep(1)
            except KeyboardInterrupt:
                print("Scheduler stopped.")
        elif choice == "11":
            break
        else:
            print("Invalid option")
    conn.enable_device()
    conn.disconnect()

def manual_menu():
    print("\nManual Device Menu:")
    for key, device in predefined_devices.items():
        print(f"{key}. {device['name']} - {device['ip']}")
    choice = input("Enter your choice: ")
    if choice in predefined_devices:
        device = predefined_devices[choice]
        fetch_attendance(device["ip"], device["name"])
    else:
        print("Invalid choice!")

def custom_ip_menu():
    custom_ip = input("Enter device IP: ")
    custom_name = input("Enter a name for the device: ")
    fetch_attendance(custom_ip, custom_name)

def scan_network():
    network = input("Enter network to scan (e.g., 192.168.1.0/24): ")
    print("Scanning network for devices...")
    for ip in ipaddress.IPv4Network(network):
        ip_str = str(ip)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((ip_str, 4370))
            if result == 0:
                print(f"Found active device at {ip_str}")
                name = input(f"Enter name for device at {ip_str}: ")
                fetch_attendance(ip_str, name)
            sock.close()
        except:
            continue

def setup_error_logging():
    logging.basicConfig(filename="error_log.txt", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    setup_error_logging()
    while True:
        print("\nMain Menu")
        print("1. Fetch All Branch Logs (Auto)")
        print("2. Manual Device Selection")
        print("3. Enter Custom IP")
        print("4. Scan Network for Devices")
        print("5. Exit")
        choice = input("Choose option (1-5): ")
        if choice == "1":
            fetch_attendance_from_all_devices()
        elif choice == "2":
            manual_menu()
        elif choice == "3":
            custom_ip_menu()
        elif choice == "4":
            scan_network()
        elif choice == "5":
            print("Exiting program.")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
