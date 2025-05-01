document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("changeColorBtn");
  
    button.addEventListener("click", async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
      chrome.tabs.update(tab.id, {
        url: "localhost:8080/IndexPage"
      });
    });
  });