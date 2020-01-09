module.exports = {
    "env": {
        "browser": true,
        "es6": true,
        "jest": true,
        "jquery": true
    },
    "extends": [
        "eslint:recommended",
        "plugin:react/recommended"
    ],
    "parserOptions": {
        "sourceType": "module",
        ecmaVersion: 2017,
        ecmaFeatures: {
            experimentalObjectRestSpread: true,
        }
    },
    "rules": {
        "indent": [
            "error",
            2
        ],
        "linebreak-style": [
            "error",
            "unix"
        ],
        "quotes": [
            "error",
            "single"
        ],
        "react/prop-types": 0,
        "semi": [
            "error",
            "never"
        ]
    }
};
