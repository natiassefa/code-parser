"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.notFound = exports.errorHandler = void 0;
const errorHandler = (err, req, res, next) => {
    let error = { ...err };
    error.message = err.message;
    console.error(err);
    if (err.name === 'CastError') {
        const message = 'Resource not found';
        error = { name: 'CastError', message, statusCode: 404 };
    }
    if (err.name === 'ValidationError') {
        const message = 'Validation Error';
        error = { name: 'ValidationError', message, statusCode: 400 };
    }
    res.status(error.statusCode || 500).json({
        success: false,
        error: error.message || 'Server Error',
        timestamp: new Date().toISOString(),
        path: req.originalUrl
    });
};
exports.errorHandler = errorHandler;
const notFound = (req, res, next) => {
    res.status(404).json({
        success: false,
        error: `Route ${req.originalUrl} not found`,
        timestamp: new Date().toISOString(),
        path: req.originalUrl
    });
};
exports.notFound = notFound;
