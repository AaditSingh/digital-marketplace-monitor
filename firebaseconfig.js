// firebaseConfig.js (create this file separately and import it in others)
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-app.js";
import { getAuth, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyDQ4SYNUgD2GxI_1XwwN4zihJMsy3c3BHQ",
    authDomain: "authen1234-67d08.firebaseapp.com",
    projectId: "authen1234-67d08",
    storageBucket: "authen1234-67d08.appspot.com",
    messagingSenderId: "335923850084",
    appId: "1:335923850084:web:authen1234-67d08"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export { auth, provider };