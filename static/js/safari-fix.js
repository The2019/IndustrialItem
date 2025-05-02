/**
 * Safari navigation fix for Flask applications
 * This script helps prevent Safari from getting stuck loading pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Force page reload on back/forward navigation (Safari cache issue)
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            window.location.reload();
        }
    });

    // Add timestamp to all navigation URLs to prevent caching
    const links = document.querySelectorAll('a[href]:not([target="_blank"]):not([href^="#"])');
    links.forEach(function(link) {
        link.addEventListener('click', function(event) {
            // Don't process if this isn't a same-site navigation
            if (this.hostname !== window.location.hostname) return;
            
            // Add timestamp parameter to prevent caching
            let url = this.href;
            const timestamp = new Date().getTime();
            
            if (url.indexOf('?') === -1) {
                url += '?_=' + timestamp;
            } else {
                url += '&_=' + timestamp;
            }
            
            // Replace the href with the timestamped URL
            this.href = url;
            
            // Show loading indicator
            const loadingIndicator = document.createElement('div');
            loadingIndicator.style.position = 'fixed';
            loadingIndicator.style.top = '0';
            loadingIndicator.style.left = '0';
            loadingIndicator.style.width = '100%';
            loadingIndicator.style.height = '3px';
            loadingIndicator.style.backgroundColor = '#66A5AD';
            loadingIndicator.style.zIndex = '9999';
            document.body.appendChild(loadingIndicator);
            
            // Do not prevent default - let the browser navigate with the new URL
        });
    });
    
    // Fix form submissions
    const forms = document.querySelectorAll('form:not([target="_blank"])');
    forms.forEach(function(form) {
        // Add hidden timestamp field to prevent caching on form submissions
        let input = document.createElement('input');
        input.type = 'hidden';
        input.name = '_timestamp';
        input.value = new Date().getTime();
        form.appendChild(input);
        
        // Attach submit handler
        form.addEventListener('submit', function() {
            // Show loading indicator
            const loadingIndicator = document.createElement('div');
            loadingIndicator.style.position = 'fixed';
            loadingIndicator.style.top = '0';
            loadingIndicator.style.left = '0';
            loadingIndicator.style.width = '100%';
            loadingIndicator.style.height = '3px';
            loadingIndicator.style.backgroundColor = '#66A5AD';
            loadingIndicator.style.zIndex = '9999';
            document.body.appendChild(loadingIndicator);
        });
    });
}); 