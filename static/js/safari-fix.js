/**
 * Safari navigation fix for Flask applications
 * This script helps prevent Safari from getting stuck loading pages
 * Production server version
 */

// Configuration for production environments
const PRODUCTION = true; // Set to true for production deployment

document.addEventListener('DOMContentLoaded', function() {
    // Run on page load to ensure proper state
    handlePageLoad();
    
    // Force page reload on back/forward navigation (Safari cache issue)
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            window.location.reload();
        }
    });

    // Fix links - more aggressive in production
    fixLinks();
    
    // Fix forms
    fixForms();
});

function handlePageLoad() {
    // Clear any stuck loading state
    document.body.classList.remove('loading');
    
    // Force a reload if URL contains _=timestamp but no content is loaded
    if (window.location.search.includes('_=') && document.body.children.length < 2) {
        window.location.reload(true);
    }
}

function fixLinks() {
    // Get all links that stay within the site
    const links = document.querySelectorAll('a[href]:not([target="_blank"]):not([href^="#"]):not([href^="javascript"])');
    
    links.forEach(function(link) {
        // Remove existing click handlers
        const clone = link.cloneNode(true);
        link.parentNode.replaceChild(clone, link);
        
        // Add our handler
        clone.addEventListener('click', function(event) {
            // Don't process external links
            if (this.hostname !== window.location.hostname) return;
            
            // Prevent default navigation
            event.preventDefault();
            
            // Show loading indicator
            document.body.classList.add('loading');
            
            // Add timestamp to bust cache
            let url = this.href;
            const timestamp = new Date().getTime();
            
            url = url.split('#')[0]; // Remove any hash
            if (url.indexOf('?') === -1) {
                url += '?_=' + timestamp;
            } else {
                url += '&_=' + timestamp;
            }
            
            // In production - use fetch first to "warm up" the request
            if (PRODUCTION) {
                fetch(url, {
                    method: 'GET',
                    headers: {
                        'X-Safari-Fix': '1',
                        'Cache-Control': 'no-cache, no-store, must-revalidate'
                    },
                    cache: 'no-store'
                }).then(() => {
                    // After pre-fetching, navigate
                    setTimeout(function() {
                        window.location.href = url;
                    }, 100);
                }).catch(() => {
                    // If fetch fails, still navigate
                    window.location.href = url;
                });
            } else {
                // Direct navigation for development
                window.location.href = url;
            }
        });
    });
}

function fixForms() {
    // Get all forms
    const forms = document.querySelectorAll('form:not([target="_blank"])');
    
    forms.forEach(function(form) {
        // Skip already processed forms
        if (form.dataset.safariFix === 'true') return;
        form.dataset.safariFix = 'true';
        
        // Add hidden timestamp field
        let input = document.createElement('input');
        input.type = 'hidden';
        input.name = '_timestamp';
        input.value = new Date().getTime();
        form.appendChild(input);
        
        // Add hidden anti-cache field
        let nocache = document.createElement('input');
        nocache.type = 'hidden';
        nocache.name = '_nocache';
        nocache.value = 'true';
        form.appendChild(nocache);
        
        // Modify form submission
        form.addEventListener('submit', function(event) {
            // Only for non-AJAX forms
            if (form.dataset.ajax === 'true') return;
            
            // Show loading indicator
            document.body.classList.add('loading');
            
            // Update timestamp value
            const timestampField = form.querySelector('input[name="_timestamp"]');
            if (timestampField) {
                timestampField.value = new Date().getTime();
            }
        });
    });
}

// Add CSS for loading indicator if not already present
if (!document.getElementById('safari-fix-styles')) {
    const style = document.createElement('style');
    style.id = 'safari-fix-styles';
    style.textContent = `
        body.loading {
            cursor: wait;
            pointer-events: none;
        }
        
        body.loading::after {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background-color: #66A5AD;
            animation: safari-loading 2s infinite ease-in-out;
            z-index: 9999;
        }
        
        @keyframes safari-loading {
            0% { width: 0%; left: 0; }
            50% { width: 50%; left: 25%; }
            100% { width: 0%; left: 100%; }
        }
    `;
    document.head.appendChild(style);
} 