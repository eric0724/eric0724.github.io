// firebase.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import { getDatabase, ref, get, set } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-database.js";

const firebaseConfig = {
    apiKey: "AIzaSyCE-SnHpd863QhOsyOqePxzAp4dn6qIFJY",
    authDomain: "gamesfirebase-8d2cb.firebaseapp.com",
    databaseURL: "https://gamesfirebase-8d2cb-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "gamesfirebase-8d2cb",
    storageBucket: "gamesfirebase-8d2cb.firebasestorage.app",
    messagingSenderId: "524485096250",
    appId: "1:524485096250:web:bf3e5d5cade284d9575603"
};

const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

export { database, ref, get, set };

/*
// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword   } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyCE-SnHpd863QhOsyOqePxzAp4dn6qIFJY",
  authDomain: "gamesfirebase-8d2cb.firebaseapp.com",
  projectId: "gamesfirebase-8d2cb",
  storageBucket: "gamesfirebase-8d2cb.firebasestorage.app",
  messagingSenderId: "524485096250",
  appId: "1:524485096250:web:bf3e5d5cade284d9575603"
};
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
document.getElementById("sum").addEventListener("click", function (even) {
  const email = document.getElementById("inputName").value.trim();
  const password = 1;
  /*
  if (inputName !== "") {
      if (namelist.includes(inputName)) {
          alert("名稱已使用（可以繼續使用）");
      } else {
          namelist.push(inputName);
          set(nameRef, namelist); // 更新資料庫
      }
  } else {
      alert("未輸入名稱");
  }
      
     
  createUserWithEmailAndPassword(auth, email, password)
    .then((userCredential) => {
      // Signed up 
      const user = userCredential.user;
      window.alert(user);
      // ...
    })
    .catch((error) => {
      const errorCode = error.code;
      const errorMessage = error.message;
      window.alert(errorCode);
      window.alert(errorMessage);
      // ..
    });
});*/