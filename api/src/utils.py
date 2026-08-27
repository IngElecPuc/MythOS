import time
import sys

def update_progress(current, total, start_time, update_interval=10, bar_width=30):
    """
    Calculates and prints the progress %, progress bar, and ETA.
    Executes only on iterations that match the specified update interval.
    """
    # Only process if it is the final iteration or matches the interval
    if current % update_interval != 0 and current != total:
        return

    # Avoid division by zero on the very first iteration without progress
    if current == 0:
        return

    # 1. Progress Calculations
    percentage = (current / total) * 100
    blocks = int(bar_width * current // total)
    bar = "█" * blocks + "-" * (bar_width - blocks)

    # 2. Time Calculations (Speed and ETA)
    elapsed_time = time.time() - start_time
    items_per_second = current / elapsed_time
    remaining_items = total - current
    
    # Calculate ETA in remaining seconds
    eta_seconds = remaining_items / items_per_second if items_per_second > 0 else 0

    # 3. Format time legibly (MM:SS or HH:MM:SS)
    if eta_seconds >= 3600:
        eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
    else:
        eta_str = time.strftime("%M:%S", time.gmtime(eta_seconds))

    # 4. Print on the same line using carriage return (\r)
    sys.stdout.write(f"\rProgress: [{bar}] {percentage:.1f}% | ETA: {eta_str} | {current}/{total} iters")
    sys.stdout.flush()

# ==========================================
# USAGE EXAMPLE
# ==========================================
if __name__ == "__main__":
    total_iterations = 200
    
    print("Starting heavy task...")
    start_time = time.time()

    for i in range(1, total_iterations + 1):
        # --- Simulating your heavy code/process ---
        time.sleep(0.05) 
        # ------------------------------------------

        # Call the function, recalculating every 15 iterations
        update_progress(
            current=i, 
            total=total_iterations, 
            start_time=start_time, 
            update_interval=15
        )
        
    print("\nTask completed successfully!")
