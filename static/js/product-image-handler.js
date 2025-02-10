// Constants for image processing
const STANDARD_WIDTH = 800;
const STANDARD_HEIGHT = 800;
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/gif'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

// Function to show error messages
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-2';
    errorDiv.innerHTML = message;
    errorContainer.appendChild(errorDiv);
    
    // Removeing the error message after 5 seconds
    setTimeout(() => errorDiv.remove(), 5000);
}

// Function to show image preview
function showImagePreview(imageUrl) {
    const previewContainer = document.getElementById('image-preview-container');
    const previewDiv = document.createElement('div');
    previewDiv.className = 'relative';
    
    const img = document.createElement('img');
    img.src = imageUrl;
    img.className = 'w-full h-32 object-cover rounded-lg';
    
    previewDiv.appendChild(img);
    previewContainer.appendChild(previewDiv);
}

// Function to process images before uploading
async function processImages(files) {
    const processedFiles = [];
    const errors = [];
    
    // for clearing the previous previews
    document.getElementById('image-preview-container').innerHTML = '';
    document.getElementById('error-container').innerHTML = '';

    for (const file of Array.from(files)) {
        if (!ACCEPTED_TYPES.includes(file.type)) {
            showError(`${file.name} is not a supported image type`);
            continue;
        }

        if (file.size > MAX_FILE_SIZE) {
            showError(`${file.name} exceeds 5MB size limit`);
            continue;
        }

        try {
            const processedFile = await new Promise((resolve, reject) => {
                const img = new Image();
                const reader = new FileReader();

                reader.onload = function(e) {
                    img.src = e.target.result;
                };

                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');

                    // calculating dimension for center
                    let sourceX = 0;
                    let sourceY = 0;
                    let sourceWidth = img.width;
                    let sourceHeight = img.height;

                    if (img.width / img.height > 1) {
                        sourceWidth = img.height;
                        sourceX = (img.width - sourceWidth) / 2;
                    } else {
                        sourceHeight = img.width;
                        sourceY = (img.height - sourceHeight) / 2;
                    }

                    canvas.width = STANDARD_WIDTH;
                    canvas.height = STANDARD_HEIGHT;

                    ctx.drawImage(
                        img,
                        sourceX, sourceY,
                        sourceWidth, sourceHeight,
                        0, 0,
                        STANDARD_WIDTH, STANDARD_HEIGHT
                    );

                    // for showing the preview
                    showImagePreview(canvas.toDataURL('image/jpeg'));

                    canvas.toBlob(
                        (blob) => {
                            const processedFile = new File(
                                [blob],
                                file.name,
                                { type: 'image/jpeg', lastModified: new Date().getTime() }
                            );
                            resolve(processedFile);
                        },
                        'image/jpeg',
                        0.9
                    );
                };

                img.onerror = reject;
            });

            processedFiles.push(processedFile);
        } catch (error) {
            showError(`Error processing ${file.name}`);
        }
    }

    return processedFiles;
}

// Handleing the form submissions
document.getElementById('product-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('product_images');
    const processedFiles = await processImages(fileInput.files);
    
    if (processedFiles.length === 0) {
        showError('No valid images to upload');
        return;
    }

    const formData = new FormData(this);
    
    // Removeing original files and adding processed files to it
    formData.delete('product_images');
    processedFiles.forEach(file => {
        formData.append('product_images', file);
    });

    try {
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });

        if (response.ok) {
            window.location.href = response.url; // Redirecting to success page
        } else {
            showError('Error uploading images. Please try again.');
        }
    } catch (error) {
        showError('Network error. Please try again.');
    }
});

// For handleing file input change
document.getElementById('product_images').addEventListener('change', function(e) {
    processImages(this.files);
});