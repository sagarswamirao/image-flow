import React, {useState, useEffect, useRef} from 'react';
import axios from 'axios';
import './ImageUploader.css';
import toast, { Toaster } from 'react-hot-toast';

const Alert = ({ children }) => (
  <div className="error-alert">
    {children}
  </div>
);
const Loader = () => (
    <div className="loader-overlay">
      <div className="loader"></div>
    </div>
);

const ImagePreview = ({ file, index }) => {
  const [preview, setPreview] = useState('');

  useEffect(() => {
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result);
    };
    reader.readAsDataURL(file);

    return () => {
      reader.abort();
    };
  }, [file]);

  return (
    <div className="image-preview">
      {preview && <img src={preview} alt={`Preview ${index + 1}`} />}
    </div>
  );
};

const ImageUploader = () => {
  const [files, setFiles] = useState([]);
  const [email, setEmail] = useState('');
  const [metadata, setMetadata] = useState([]);
  const [openAccordions, setOpenAccordions] = useState([]);
  const [imageErrors, setImageErrors] = useState({});
  const [isSubmitDisabled, setIsSubmitDisabled] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const selectedFiles = [...event.target.files];
    setFiles(selectedFiles);
    setImageErrors({});

    const newMetadata = selectedFiles.map(file => ({
      image_name: file.name,
      filters: {
        resize: { width: '', height: '' },
        crop: { top: '', left: '', width: '', height: '' },
        rotate: '',
        brightness: {
          enabled: false,
          value: 0
        },
        grayscale: false,
        flip: ''
      }
    }));

    setMetadata(newMetadata);
    setOpenAccordions([0]);
  };

  const handleEmailChange = (event) => {
    setEmail(event.target.value);
  };

  const hasAppliedFilters = (imageMetadata) => {
    const filters = imageMetadata.filters;

    const hasResize = filters.resize.width || filters.resize.height;
    const hasCrop = Object.values(filters.crop).some(value => value !== '');
    const hasRotate = filters.rotate !== '';
    const hasBrightness = filters.brightness.enabled && filters.brightness.value !== 0;
    const hasGrayscale = filters.grayscale;
    const hasFlip = filters.flip !== '';

    return hasResize || hasCrop || hasRotate || hasBrightness || hasGrayscale || hasFlip;
  };

  const validateAllImages = () => {
    let hasErrors = false;
    const newErrors = {};

    metadata.forEach((meta, index) => {
      const hasFilters = hasAppliedFilters(meta);
      if (!hasFilters) {
        newErrors[index] = 'Please apply at least one filter';
        hasErrors = true;
      }
    });

    setImageErrors(newErrors);
    return !hasErrors;
  };

  const handleMetadataChange = (index, field, value) => {
    const newMetadata = [...metadata];
    newMetadata[index] = {
      ...newMetadata[index],
      [field]: value
    };
    setMetadata(newMetadata);
  };

  const handleFilterChange = (index, filter, value) => {
    const newMetadata = [...metadata];
    if (filter === 'brightness') {
      if (typeof value === 'boolean') {
        newMetadata[index].filters.brightness.enabled = value;
        if (!value) {
          newMetadata[index].filters.brightness.value = 0;
        }
      } else {
        newMetadata[index].filters.brightness.value = value;
      }
    } else {
      newMetadata[index].filters[filter] = value;
    }
    setMetadata(newMetadata);
    setImageErrors({});
  };

  const toggleAccordion = (index) => {
    setOpenAccordions(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index);
      } else {
        return [...prev, index];
      }
    });
  };

  const transformMetadata = (metadata) => {
    return metadata.map(item => {
      const filters = [];

      if (item.filters.resize.width || item.filters.resize.height) {
        filters.push({
          filter_type: "resize",
          filter_value: {
            width: item.filters.resize.width ? parseInt(item.filters.resize.width) : null,
            height: item.filters.resize.height ? parseInt(item.filters.resize.height) : null
          }
        });
      }

      if (Object.values(item.filters.crop).some(value => value !== '')) {
        filters.push({
          filter_type: "crop",
          filter_value: {
            top: parseInt(item.filters.crop.top) || 0,
            left: parseInt(item.filters.crop.left) || 0,
            width: parseInt(item.filters.crop.width) || 0,
            height: parseInt(item.filters.crop.height) || 0
          }
        });
      }

      if (item.filters.rotate !== '') {
        filters.push({
          filter_type: "rotate",
          filter_value: parseInt(item.filters.rotate)
        });
      }

      if (item.filters.brightness.enabled && item.filters.brightness.value !== 0) {
        filters.push({
          filter_type: "brightness",
          filter_value: parseInt(item.filters.brightness.value)
        });
      }

      if (item.filters.grayscale) {
        filters.push({
          filter_type: "grayscale",
          filter_value: {}
        });
      }

      if (item.filters.flip) {
        filters.push({
          filter_type: "flip",
          filter_value: { direction: item.filters.flip }
        });
      }

      return {
        image_name: item.image_name,
        filters: filters
      };
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validateAllImages()) {
      setIsSubmitDisabled(true);
      return;
    }
    setIsLoading(true);
    setIsSubmitting(true);
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const transformedData = {
      email,
      imagesMetadata: transformMetadata(metadata)
    };

    formData.append('metadata', JSON.stringify(transformedData));
    console.log(transformedData);

    try {
      // const response = await axios.post('http://localhost:5000/upload-images', formData, {
      //       headers: {
      //           'Content-Type': 'multipart/form-data'
      //       }
      //   });
        const response = await axios.post('http://34.66.13.157/upload-images', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        console.log(response)
        if (response.status === 200) {
            // alert('Images uploaded successfully!');
          toast.success('Images uploaded successfully!');
          setFiles([]);
          setEmail('');
          setMetadata([]);
          setOpenAccordions([]);
          setImageErrors({});
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        } else {
          toast.error('Failed to upload images.');
        }
    } catch (error) {
      toast.error('Failed to upload images.');
    }
    finally {
      setIsSubmitting(false);
      setIsLoading(false);
    }
  };

  return (
    <div className="image-uploader">
      <Toaster position="top-right" />
      {isLoading && <Loader />}
      <h2 className="title">Upload Images</h2>
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label className="form-label">
            Email:
            <input
              type="email"
              value={email}
              onChange={handleEmailChange}
              required
              className="form-input"
            />
          </label>
        </div>

        <div className="form-group">
          <label className="form-label">
            Select Images:
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleFileChange}
              required
              className="file-input"
              ref={fileInputRef}
            />
          </label>
        </div>

        <div className="images-container">
          {files.map((file, index) => (
            <div key={index} className="image-section">
              <div
                className={`accordion-header ${imageErrors[index] ? 'has-error' : ''}`}
                onClick={() => toggleAccordion(index)}
              >
                <div className="image-info">
                  <ImagePreview file={file} index={index} />
                  <span className="image-name">{file.name}</span>
                  {imageErrors[index] && (
                    <span className="error-message">{imageErrors[index]}</span>
                  )}
                </div>
                <span className={`accordion-icon ${openAccordions.includes(index) ? 'open' : ''}`}>
                  ▼
                </span>
              </div>

              {openAccordions.includes(index) && (
                <div className="metadata-section">
                  <div className="form-group">
                    <label className="form-label">
                      Image Name:
                      <input
                        type="text"
                        value={metadata[index]?.image_name || ''}
                        onChange={(e) => handleMetadataChange(index, 'image_name', e.target.value)}
                        required
                        className="form-input"
                      />
                    </label>
                  </div>

                  <div className="filter-group">
                    <h4 className="filter-title">Resize</h4>
                    <div className="filter-inputs">
                      <input
                        type="number"
                        placeholder="Width"
                        value={metadata[index]?.filters.resize.width}
                        onChange={(e) => handleFilterChange(index, 'resize', {
                          ...metadata[index]?.filters.resize,
                          width: e.target.value
                        })}
                        className="form-input"
                      />
                      <input
                        type="number"
                        placeholder="Height"
                        value={metadata[index]?.filters.resize.height}
                        onChange={(e) => handleFilterChange(index, 'resize', {
                          ...metadata[index]?.filters.resize,
                          height: e.target.value
                        })}
                        className="form-input"
                      />
                    </div>
                  </div>

                  <div className="filter-group">
                    <h4 className="filter-title">Crop</h4>
                    <div className="filter-inputs">
                      <input
                        type="number"
                        placeholder="Top"
                        value={metadata[index]?.filters.crop.top}
                        onChange={(e) => handleFilterChange(index, 'crop', {
                          ...metadata[index]?.filters.crop,
                          top: e.target.value
                        })}
                        className="form-input"
                      />
                      <input
                        type="number"
                        placeholder="Left"
                        value={metadata[index]?.filters.crop.left}
                        onChange={(e) => handleFilterChange(index, 'crop', {
                          ...metadata[index]?.filters.crop,
                          left: e.target.value
                        })}
                        className="form-input"
                      />
                      <input
                        type="number"
                        placeholder="Width"
                        value={metadata[index]?.filters.crop.width}
                        onChange={(e) => handleFilterChange(index, 'crop', {
                          ...metadata[index]?.filters.crop,
                          width: e.target.value
                        })}
                        className="form-input"
                      />
                      <input
                        type="number"
                        placeholder="Height"
                        value={metadata[index]?.filters.crop.height}
                        onChange={(e) => handleFilterChange(index, 'crop', {
                          ...metadata[index]?.filters.crop,
                          height: e.target.value
                        })}
                        className="form-input"
                      />
                    </div>
                  </div>

                  <div className="filter-group">
                    <label className="form-label">
                      Rotate:
                      <input
                        type="number"
                        placeholder="Angle (degrees)"
                        value={metadata[index]?.filters.rotate}
                        onChange={(e) => handleFilterChange(index, 'rotate', e.target.value)}
                        className="form-input"
                      />
                    </label>
                  </div>

                  <div className="filter-group">
                    <label className="form-label checkbox-label">
                      Brightness:
                      <input
                        type="checkbox"
                        checked={metadata[index]?.filters.brightness.enabled}
                        onChange={(e) => handleFilterChange(index, 'brightness', e.target.checked)}
                        className="checkbox-input"
                      />
                    </label>
                    {metadata[index]?.filters.brightness.enabled && (
                      <div className="brightness-control">
                        <div className="range-input-container">
                          <input
                            type="range"
                            min="-100"
                            max="100"
                            value={metadata[index]?.filters.brightness.value}
                            onChange={(e) => handleFilterChange(index, 'brightness', parseInt(e.target.value))}
                            className="range-input"
                          />
                          <input
                            type="number"
                            value={metadata[index]?.filters.brightness.value}
                            onChange={(e) => handleFilterChange(index, 'brightness', parseInt(e.target.value))}
                            className="brightness-value-input"
                            min="-100"
                            max="100"
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="filter-group">
                    <label className="form-label checkbox-label">
                      Grayscale:
                      <input
                        type="checkbox"
                        checked={metadata[index]?.filters.grayscale}
                        onChange={(e) => handleFilterChange(index, 'grayscale', e.target.checked)}
                        className="checkbox-input"
                      />
                    </label>
                  </div>

                  <div className="filter-group">
                    <label className="form-label">
                      Flip:
                      <select
                        value={metadata[index]?.filters.flip}
                        onChange={(e) => handleFilterChange(index, 'flip', e.target.value)}
                        className="select-input"
                      >
                        <option value="">None</option>
                        <option value="horizontal">Horizontal</option>
                        <option value="vertical">Vertical</option>
                      </select>
                    </label>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {files.length > 0 && (
          <div className="button-group">
            <button
              type="submit"
              className="submit-button"
              // disabled={isSubmitDisabled}
            >
              Upload Images
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

export default ImageUploader;