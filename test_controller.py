import struct
import sys
import os

def main():
    device_path = '/dev/input/js0'
    if not os.path.exists(device_path):
        print(f"Error: {device_path} does not exist. Is the controller connected?")
        sys.exit(1)

    print(f"Successfully opened {device_path}!")
    print("Reading controller events. Press buttons or move sticks (Ctrl+C to exit)...")
    print("-" * 50)
    
    # Event format: 32-bit timestamp, 16-bit value, 8-bit type, 8-bit number
    event_format = 'IhBB'
    event_size = struct.calcsize(event_format)

    try:
        with open(device_path, 'rb') as f:
            while True:
                event_data = f.read(event_size)
                if not event_data:
                    break
                time, value, event_type, number = struct.unpack(event_format, event_data)
                
                # event_type definitions:
                # 0x01: Button
                # 0x02: Axis
                # 0x80: Init flag (or'ed with type)
                is_init = bool(event_type & 0x80)
                actual_type = event_type & ~0x80
                
                type_str = "Unknown"
                if actual_type == 1:
                    type_str = "Button"
                elif actual_type == 2:
                    type_str = "Axis"
                
                init_str = " (Init)" if is_init else ""
                
                print(f"Time: {time:10d}ms | {type_str:6s} {number:3d} | Value: {value:6d}{init_str}")
    except PermissionError:
        print(f"Permission Error: Run this test script with sudo, or add your user to the 'input' group.")
    except KeyboardInterrupt:
        print("\nExiting controller test.")

if __name__ == '__main__':
    main()
