import React from 'react';
import './Footer.css';

const Footer = () => {
    return (
        <footer className="footer">
            <div className="footer-center">
                Created with ❤️
            </div>
            <div className="footer-row">
                <div className="footer-left">
                    <strong>Pavan Sai Appari</strong> -
                    <a href="https://github.com/pavnsai" target="_blank" rel="noopener noreferrer"
                       className="footer-link"> GitHub</a> |
                    <a href="https://www.linkedin.com/in/pavan1810/" target="_blank" rel="noopener noreferrer"
                       className="footer-link"> LinkedIn</a>
                </div>
                <div className="footer-right">
                    <strong>Sagar Swami Rao Kulkarni</strong> -
                    <a href="https://github.com/sagarswamiraokulkarni" target="_blank" rel="noopener noreferrer"
                       className="footer-link"> GitHub</a> |
                    <a href="https://www.linkedin.com/in/sagarswamirao/" target="_blank" rel="noopener noreferrer"
                           className="footer-link"> LinkedIn</a>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
