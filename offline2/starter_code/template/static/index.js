function app() {
  return {
    /* This is the main app object containing all the application state and methods. */
    // The following properties are used to store the state of the application

    // results of cache latency measurements
    latencyResults: null,
    // local collection of trace data
    traceData: [],
    // Local collection of heapmap images
    heatmapImages: [],

    // Current status message
    status: "",
    // Is any worker running?
    isCollecting: false,
    // Is the status message an error?
    statusIsError: false,
    // Show trace data in the UI?
    showingTraces: false,

    // Collect latency data using warmup.js worker
    async collectLatencyData() {
      this.isCollecting = true;
      this.status = "Collecting latency data...";
      this.latencyResults = null;
      this.statusIsError = false;
      this.showingTraces = false;

      try {
        // Create a worker
        let worker = new Worker("warmup.js");

        // Start the measurement and wait for result
        const results = await new Promise((resolve) => {
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
        });

        // Update results
        this.latencyResults = results;
        this.status = "Latency data collection complete!";

        // Terminate worker
        worker.terminate();
      } catch (error) {
        console.error("Error collecting latency data:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },

    // Collect trace data using worker.js and send to backend
    async collectTraceData() {
      /* Implement this function to collect trace data. */
      this.isCollecting = true;
      this.status = "Collecting trace data...";
      this.traceData = [];
      this.statusIsError = false;
      this.showingTraces = false;
      
      try {
        /* 1. Create a worker to run the sweep function. */
        let worker = new Worker("worker.js");
      
        const results = await new Promise((resolve) => {
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
        });
      
        /* 2. Collect the trace data from the worker.*/
        this.traceData = results;
        console.log(results);
        this.status = "Trace collected";
        worker.terminate();
      
        /* 3. Send the trace data to the backend for temporary storage and heatmap generation.*/
        await fetch("/collect_trace", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(results),
        })
          .then((res) => res.json())
          .then((data) => {
            console.log("Backend responded:", data);
            /* 4. Fetch the heatmap from the backend and add it to the local collection.*/
            if (data.heatmaps) {
              this.heatmapImages = data.heatmaps.map(item => ({
                image: `data:image/png;base64,${item.image}`,
                stats: `Min: ${item.min}, Max: ${item.max}, Range: ${item.range}, Samples: ${item.samples}`
              }));
              this.showingTraces = true;
            }              
          })
          .catch((err) => {
            console.error("Error uploading trace data:", err);
          });
      /* 5. Handle errors and update the status.*/
      } 
      catch (error) {
        console.error("Error collecting trace data:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } 
      finally {
        this.isCollecting = false;
      }
    },

    async downloadTraces() {
      this.status = "Downloading trace data...";
      this.statusIsError = false;

      try {
        const response = await fetch('/download_traces');
        if (!response.ok) throw new Error("Failed to download trace data");

        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "trace_data.json";
        link.click();
        URL.revokeObjectURL(url);

        this.status = "Download complete!";
      } catch (error) {
        console.error("Download error:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      }
    },

    async clearResults() {
      this.status = "Clearing results...";
      this.statusIsError = false;

      try {
        const response = await fetch("/api/clear_results", {
          method: "POST",
        });

        if (!response.ok) throw new Error("Failed to clear results");

        this.traceData = [];
        this.heatmapImages = [];
        this.showingTraces = false;
        this.status = "cleared";
      } catch (error) {
        console.error("Clear error:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      }
    },

    // // Download the trace data as JSON (array of arrays format for ML)
    // async downloadTraces() {
    //     /* 
    //     * Implement this function to download the trace data.
    //     * 1. Fetch the latest data from the backend API.
    //     * 2. Create a download file with the trace data in JSON format.
    //     * 3. Handle errors and update the status.
    //     */
    // },

    // // Clear all results from the server
    // async clearResults() {
    //     /* 
    //     * Implement this function to clear all results from the server.
    //     * 1. Send a request to the backend API to clear all results.
    //     * 2. Clear local copies of trace data and heatmaps.
    //     * 3. Handle errors and update the status.
    //     */
    // },
  };
}
