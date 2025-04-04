// Add event listener after the DOM is loaded
document.addEventListener('DOMContentLoaded', (event) => {
    // Add listener for the clear button
    const clearButton = document.getElementById('clear-btn');
    const textArea = document.getElementById('text');
    if (clearButton && textArea) {
        clearButton.addEventListener('click', () => {
            textArea.value = ''; // Clear the text area
            textArea.focus(); // Optionally focus the text area after clearing
        });
    }
});

async function handleSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const resultSection = document.getElementById('result-section');

    // Reset previous state
    submitBtn.disabled = true;
    loading.style.display = 'block';
    errorMessage.style.display = 'none';
    errorMessage.textContent = '';
    resultSection.innerHTML = ''; // Clear previous results

    try {
        const formData = new FormData(form);
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json(); // Always expect JSON

        if (!response.ok) {
            // Use error message from JSON response if available
            throw new Error(data.detail || data.error || `HTTP error! status: ${response.status}`);
        }

        // Process successful JSON response
        displayResults(data.results);

    } catch (error) {
        console.error('Error submitting form:', error);
        errorMessage.textContent = error.message || 'An unexpected error occurred.';
        errorMessage.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        loading.style.display = 'none';
    }
}

function displayResults(results) {
    const resultSection = document.getElementById('result-section');
    resultSection.innerHTML = ''; // Clear previous results first

    if (results && results.length > 0) {
        const resultText = results.join('\n'); // Join with actual newlines

        // Create the result container div
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result';

        // Create and add the heading
        const heading = document.createElement('h3');
        heading.textContent = `Result: (found ${results.length})`;
        resultDiv.appendChild(heading);

        // Create the editable paragraph
        const paragraph = document.createElement('p');
        paragraph.id = 'result-text';
        paragraph.contentEditable = true;
        paragraph.innerText = resultText; // Set text using innerText to preserve newlines
        resultDiv.appendChild(paragraph);

        // Create and add the copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-btn';
        copyButton.textContent = 'Copy';
        copyButton.onclick = () => copyToClipboard('result-text'); // Assign click handler
        resultDiv.appendChild(copyButton);

        // Add the complete result div to the section
        resultSection.appendChild(resultDiv);

    } else {
        // Handle case with no results
        const noResultDiv = document.createElement('div');
        noResultDiv.className = 'result'; // Use the same class for consistent styling
        const heading = document.createElement('h3');
        heading.textContent = 'Result: (found 0)';
        noResultDiv.appendChild(heading);
        const paragraph = document.createElement('p');
        paragraph.textContent = 'No matches found.';
        noResultDiv.appendChild(paragraph);
        resultSection.appendChild(noResultDiv);
    }
}

function copyToClipboard(elementId) {
    const textElement = document.getElementById(elementId);
    if (!textElement) {
        console.error(`Element with id ${elementId} not found`);
        return;
    }
    // Get text content from contenteditable element using innerText
    const textToCopy = textElement.innerText; 

    // Check if there is text to copy
    if (!textToCopy || textToCopy.trim() === '') {
        console.warn('Nothing to copy.');
        // Optionally provide user feedback that there is nothing to copy
        return; 
    }

    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            // Find the button more reliably within its result container
            const resultContainer = textElement.closest('.result');
            const btn = resultContainer ? resultContainer.querySelector('.copy-btn') : null;
            
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.classList.add('copied'); // Add class for animation
                btn.disabled = true;

                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied'); // Remove class after animation
                    btn.disabled = false;
                }, 1500); // Slightly shorter timeout than CSS animation if needed
            }
        })
        .catch(err => {
            console.error('Failed to copy: ', err);
            // Optionally display an error to the user
            const errorMessage = document.getElementById('error-message');
            errorMessage.textContent = 'Failed to copy results to clipboard.';
            errorMessage.style.display = 'block';
        });
}
 