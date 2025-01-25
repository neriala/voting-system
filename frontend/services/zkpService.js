import axios from "axios";

const API_URL = "http://127.0.0.1:5000";

export const verifyZKP = async (idNumber) => {
  return axios.post(`${API_URL}/zkp`, { id_number: idNumber });
};
