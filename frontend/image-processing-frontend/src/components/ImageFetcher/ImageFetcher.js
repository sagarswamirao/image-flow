import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import 'img-comparison-slider/dist/styles.css';
import './ImageFetcher.css';

const DownloadIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
);

const ExpandIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 3h6v6M14 10l7-7M9 21H3v-6M10 14l-7 7" />
    </svg>
);

const CloseIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
);

const ErrorMessage = ({ message }) => (
    <div className="error-message">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>{message}</span>
    </div>
);

const Loader = () => (
    <div className="loader-overlay">
      <div className="loader"></div>
    </div>
);

const ImageFetcher = () => {
  const { UUID: urlUUID } = useParams();
  const [uuid, setUuid] = useState(urlUUID || '');
  const [imagePairs, setImagePairs] = useState([]);
  const [showPopup, setShowPopup] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [downloadingStates, setDownloadingStates] = useState({});
  const [selectedFileName, setSelectedFileName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    import('img-comparison-slider').catch(error => {
      console.error('Error loading img-comparison-slider:', error);
      setError('Failed to load image comparison component');
    });

    if (urlUUID) {
      fetchImages(urlUUID);
    }
  }, [urlUUID]);

  const validateUUID = (uuid) => {
    return uuid && uuid.trim().length > 0;
  };

  const fetchImages = async (uuidToFetch) => {
    if (!validateUUID(uuidToFetch)) {
      setError('Please enter a valid BatchID');
      setImagePairs([]);
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://34.66.13.157/get-processed-images?batch_id=${uuidToFetch}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (!data || !Array.isArray(data.image_pairs) || data.image_pairs.length === 0) {
        setError('No images found for this UUID');
        setImagePairs([]);
        return;
      }

      setImagePairs(data.image_pairs);
    } catch (error) {
      console.error('Error fetching images:', error);
      setError('Failed to fetch images. Please try again.');
      setImagePairs([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchImages(uuid);
  };

  const handlePopup = (image, fileName) => {
    if (image) {
      setSelectedImage(image);
      setSelectedFileName(fileName);
      setShowPopup(true);
    }
  };

  const downloadImage = async (url, fileName, downloadId) => {
    if (!url) {
      setError('Image URL is missing');
      return;
    }

    try {
      setDownloadingStates(prev => ({ ...prev, [downloadId]: true }));
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = fileName || 'image.jpg';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Error downloading image:', error);
      setError('Failed to download image. Please try again.');
    } finally {
      setDownloadingStates(prev => ({ ...prev, [downloadId]: false }));
    }
  };

  const imageCount = imagePairs.length;

  return (
      <div className="gallery-container">
        <form onSubmit={handleSubmit} className="search-form">
          <div className="input-group">
            <input
                type="text"
                value={uuid}
                onChange={(e) => {
                  setUuid(e.target.value);
                  setError('');
                }}
                placeholder="Enter BatchID"
                className="uuid-input"
            />
            <button
                type="submit"
                className="fetch-button"
                disabled={isLoading}
            >
              {isLoading ? 'Loading...' : 'Fetch Images'}
            </button>
          </div>
        </form>

        {error && <ErrorMessage message={error} />}

        {isLoading && <Loader />}
        {!isLoading && imageCount > 0 && (
            <div className="image-count">
              <p>{`Number of images in this batch: ${imageCount}`}</p>
            </div>
        )}

        <div className="image-slider-grid">
          {imagePairs.map((pair, index) => (
              <div key={index} className="image-slider-card">
                <div className="file-name-header">
                  <span className="file-name">{pair.file_name || `Image ${index + 1}`}</span>
                </div>
                <div className="slider-container">
                  <img-comparison-slider>
                    <img slot="first" src={pair.before_url} alt="Before" onError={(e) => {
                      e.target.src = 'placeholder-image-url';
                      setError('Failed to load some images');
                    }}/>
                    <img slot="second" src={pair.after_url} alt="After" onError={(e) => {
                      e.target.src = 'placeholder-image-url';
                      setError('Failed to load some images');
                    }}/>
                  </img-comparison-slider>
                  <div className="slider-actions">
                    <button
                        onClick={() => handlePopup(pair.after_url, pair.file_name)}
                        className="action-button"
                        title="Zoom In"
                    >
                      <ExpandIcon />
                    </button>
                    <button
                        onClick={() => downloadImage(pair.after_url, `${pair.file_name || 'processed-image.jpg'}`, index)}
                        className="action-button"
                        title="Download After Image"
                        disabled={downloadingStates[index]}
                    >
                      {downloadingStates[index] ? <div className="loading-spinner"></div> : <DownloadIcon />}
                    </button>
                  </div>
                </div>
              </div>
          ))}
        </div>

        {showPopup && (
            <div className="modal-overlay" onClick={(e) => {
              if (e.target === e.currentTarget) setShowPopup(false);
            }}>
              <div className="modal-content">
                <div className="modal-actions">
                  <button
                      onClick={() => downloadImage(selectedImage, `${selectedFileName || 'processed-image.jpg'}`, 'modal')}
                      className="modal-button"
                      disabled={downloadingStates['modal']}
                      title="Download Image"
                  >
                    {downloadingStates['modal'] ? (
                        <span className="loading-spinner"></span>
                    ) : (
                        <DownloadIcon />
                    )}
                  </button>
                  <button
                      onClick={() => setShowPopup(false)}
                      className="modal-button"
                      title="Close"
                  >
                    <CloseIcon />
                  </button>
                </div>
                <div className="modal-image-wrapper">
                  <img
                      src={selectedImage}
                      alt="Zoomed"
                      className="modal-image"
                      onError={(e) => {
                        setError('Failed to load zoomed image');
                        setShowPopup(false);
                      }}
                  />
                </div>
              </div>
            </div>
        )}
      </div>
  );
};

export default ImageFetcher;