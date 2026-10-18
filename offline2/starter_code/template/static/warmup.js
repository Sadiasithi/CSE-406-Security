/* Find the cache line size by running `getconf -a | grep CACHE` */
const LINESIZE = 64;  

/**
 * @param {number} n - The number of cache lines to read.
 * @returns {number} - The median access time in milliseconds.
 */

function readNlines(n) {
  /* 1. Allocate a buffer of size n * LINESIZE */
  const buffer = new Uint8Array(n * LINESIZE);
  const timings = [];

  /* 2. Read each cache line (read the buffer in steps of LINESIZE) 10 times.*/
  for (let i = 0; i < 10; i++) {
    const start = performance.now();
    for (let offset = 0; offset < buffer.length; offset += LINESIZE) {
      buffer[offset];
    }

    const end = performance.now();
    /* 3. Collect total time taken in an array using `performance.now()`.*/
    timings.push(end - start);
  }
  /* 4. Return the median of the time taken in milliseconds.*/
  return calculateMedian(timings);
}

/**
 * @param {Array<number>} arr - The array of numbers to find the median of.
 * @returns {number} - The median of the array.
 */

function calculateMedian(array) {
  // Sort the array in ascending order
  array.sort((a, b) => a - b);
  const len = array.length;
  
  if (len % 2 === 0) {
    return (array[len / 2 - 1] + array[len / 2]) / 2;
  } 
  else {
    return array[Math.floor(len / 2)];
  }
}

self.addEventListener("message", function (e) {
  if (e.data === "start") {
    const results = {};

    /*Call the readNlines function for n = 1, 10, ... 10,000,000 and store the result*/
    for (let n = 1; n <= 10000000; n *= 10) {
      results[n] = readNlines(n);
    }

    self.postMessage(results);
  }
});
