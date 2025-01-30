import React from 'react';
import './HomePage.css';

const HomePage = () => {
    return (
        <div className="homepage">
            <header className="homepage-header">
                <h1>ImageFlow: Scalable Image Processor App</h1>
                <p>
                    A scalable and efficient image processing platform designed to make
                    your image editing experience seamless and user-friendly.
                </p>
            </header>

            <section className="features">
                <h2>Key Features</h2>
                <ul>
                    <li>Upload images effortlessly through a clean and intuitive interface.</li>
                    <li>Select from a variety of image modifications tailored to your needs.</li>
                    <li>Track the processing progress and receive email notifications.</li>
                    <li>Download your processed images directly through a secure link.</li>
                </ul>
            </section>

            <section className="how-it-works">
                <h2>How It Works</h2>
                <p>
                    ImageFlow combines powerful cloud technologies and dynamic scaling to handle high-demand periods without compromising performance.
                    After uploading an image, our system processes it based on your selected modifications and notifies you when it's ready.
                </p>
            </section>

            <footer className="homepage-footer">
                <p>
                    Built with React, Flask, and Google cloud technologies like GKE, Cloud function etc. for a robust and scalable experience.
                </p>
            </footer>
        </div>
    );
};

export default HomePage;
