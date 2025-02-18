// static/js/main.js
console.log("Main.js loaded");  // Add this line at the top

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM Content Loaded"); // Add this debug line
    const messages = document.querySelectorAll('[id^="message-"]');
    console.log("Messages found:", messages.length); // Add this debug line
    
    if (messages.length > 0) {
        messages.forEach(message => {
            // Add initial opacity class to enable transition
            message.classList.add('opacity-100'); // Add this line
            
            setTimeout(() => {
                console.log("Fading out message:", message.id);
                message.classList.add('opacity-0');
                
                setTimeout(() => {
                    console.log("Removing message:", message.id);
                    message.remove();
                }, 500);
            }, 5000);
        });
    }
});