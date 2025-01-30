import React, {useState} from 'react';
import {HashRouter as Router, Route, Routes} from 'react-router-dom';
import './App.css';
import ImageUploader from './components/ImageUploader/ImageUploader';
import Header from "./components/Header/Header";
import ImageFetcher from "./components/ImageFetcher/ImageFetcher";
import HomePage from "./components/HomePage/HomePage";
import Footer from "./components/Footer/Footer";

const App = () => {
    const [images, setImages] = useState([]);

    return (
        <Router>
            <div className="App">
                <Header/>
                <div className="main-content">
                    <Routes>
                        <Route path="/processed/:UUID" element={<ImageFetcher/>}/>
                        <Route
                            path="/processed"
                            element={<ImageFetcher images={images}/>}
                        />
                        <Route path="/upload" element={<ImageUploader/>}/>
                        <Route path="/" element={<HomePage/>}/>
                    </Routes>
                </div>
                <Footer/>
            </div>
        </Router>
    );
};

export default App;
