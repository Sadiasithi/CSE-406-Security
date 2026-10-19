from flask import Flask, send_from_directory, request, jsonify, send_file
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

app = Flask(__name__)

stored_traces = []
stored_heatmaps = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/collect_trace', methods=['POST'])
def collect_trace():
    global stored_traces, stored_heatmaps

    try:
        trace_data = request.get_json()

        if not isinstance(trace_data, list):
            return jsonify({"error": "Invalid data format"}), 400

        stored_traces.append(trace_data)
        trace_array = np.array(trace_data)

        min_val = int(np.min(trace_array))
        max_val = int(np.max(trace_array))
        range_val = max_val - min_val
        sample_count = trace_array.size

        fig, ax = plt.subplots(figsize=(10, 2))
        heatmap = ax.imshow(trace_array.reshape(1, -1), cmap='plasma', aspect='auto')
        ax.axis('off')

        img_io = io.BytesIO()
        plt.savefig(img_io, format='png', bbox_inches='tight', pad_inches=0)
        img_io.seek(0)

        img_base64 = base64.b64encode(img_io.read()).decode('utf-8')
        stored_heatmaps.append({
            "image": img_base64,
            "min": min_val,
            "max": max_val,
            "range": range_val,
            "samples": sample_count
        })

        return jsonify({
            "message": "Trace and heatmap stored successfully",
            "heatmaps": stored_heatmaps
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error processing trace data: {str(e)}"}), 500
        

@app.route('/download_traces', methods=['GET'])
def download_traces():
    try:
        return jsonify(stored_traces), 200
    except Exception as e:
        return jsonify({"error": f"Failed to download trace data: {str(e)}"}), 500


@app.route('/api/clear_results', methods=['POST'])
def clear_results():
    """ 
    Implement a clear results endpoint to reset stored data.
    1. Clear stored traces and heatmaps
    2. Return success/error message
    """
    try:
        global stored_traces, stored_heatmaps
        stored_traces.clear()  # Clear the traces data
        stored_heatmaps.clear()  # Clear the heatmaps data

        return jsonify({"message": "Results cleared successfully"}), 200

    except Exception as e:
        # Return a specific error message in case of failure
        return jsonify({"error": f"Failed to clear results: {str(e)}"}), 500

def clear_trace_results(driver, wait):
    """Clear all results from the backend by pressing the button."""
    clear_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Clear all results')]")
    clear_button.click()
    # Optionally, add a short sleep to allow backend to process
    import time
    time.sleep(0.5)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
