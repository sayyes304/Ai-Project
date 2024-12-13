// script.js

const fs = require("fs");

document.addEventListener("DOMContentLoaded", () => {
  feather.replace();
});

function startMeasurement() {
  // Get user input values
  const height = document.getElementById("height").value;
  const weight = document.getElementById("weight").value;

  // Create a JSON object with the input values
  const userData = {
    height: height,
    weight: weight,
  };

  // Convert the JSON object to a string
  const jsonString = JSON.stringify(userData);

  // Save JSON data to a file in the same folder
  fs.writeFile("userData.json", jsonString, (err) => {
    if (err) {
      console.error("Error saving data:", err);
    } else {
      console.log("Data successfully saved to userData.json");
      // Redirect to camera.html after successful data submission
      window.location.href = "./camera.html";
    }
  });
}
