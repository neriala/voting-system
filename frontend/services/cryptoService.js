import axios from "axios";
import { createHash } from "crypto"; // השתמש בגרסה מותאמת לדפדפן אם נדרש

// פרמטרי DH
let p, g, serverPublicKey, clientPrivateKey, clientPublicKey, sharedKey;

// קבלת פרמטרי DH מהשרת
export const fetchDHParams = async () => {
  const response = await axios.get("http://127.0.0.1:5000/dh/params");
  const params = response.data;

  // שמירת פרמטרי DH מהשרת
  p = params.p;
  g = params.g;
  serverPublicKey = params.server_public_key;

  // יצירת מפתח ציבורי ופרטי בלקוח
  clientPrivateKey = Math.floor(Math.random() * 100);
  clientPublicKey = (g ** clientPrivateKey) % p;

  return clientPublicKey;
};

// שיתוף מפתח עם השרת
export const exchangeKey = async (clientPublicKey) => {
  const response = await axios.post("http://127.0.0.1:5000/dh/exchange", {
    client_public_key: clientPublicKey,
  });

  // גזירת המפתח המשותף מתוך התשובה
  const sharedKeyBase64 = response.data.shared_key;

  // פענוח המפתח המשותף
  sharedKey = Buffer.from(sharedKeyBase64, "base64");
  return sharedKey;
};

// החזרת המפתח המשותף להצפנה
export const getSharedKey = () => sharedKey;
