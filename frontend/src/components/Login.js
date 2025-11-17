import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';

function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm();

const onSubmit = (data) => {
  if (typeof window === "undefined") return;  
  if (isRegister) {
    localStorage.setItem("user", JSON.stringify(data));
    alert("Registration successful! Please login.");
    setIsRegister(false);
  } else {

    const user = JSON.parse(localStorage.getItem("user"));
    if (user && user.email === data.email && user.password === data.password) {
      navigate("/chatbot");
    } else {
      alert("Invalid credentials");
    }
  }
};

  const validatePassword = (value) => {
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$/;
    return regex.test(value) || "Password must be at least 6 characters with uppercase, lowercase, number, and symbol";
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(to bottom, #1a1a2e, #16213e)'
    }}>
      <div style={{
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        padding: '40px',
        borderRadius: '10px',
        boxShadow: '0 0 20px rgba(0, 0, 0, 0.5)',
        width: '400px'
      }}>
        <h2 style={{ color: 'white', textAlign: 'center', marginBottom: '30px' }}>
          {isRegister ? 'Register' : 'Login'}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)}>
          {isRegister && (
            <>
              <input
                {...register('name', { required: 'Name is required' })}
                placeholder="Name"
                style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: 'none' }}
              />
              {errors.name && <p style={{ color: 'red' }}>{errors.name.message}</p>}
              <input
                {...register('id', { required: 'ID is required' })}
                placeholder="ID"
                style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: 'none' }}
              />
              {errors.id && <p style={{ color: 'red' }}>{errors.id.message}</p>}
            </>
          )}
          <input
            {...register('email', { required: 'Email is required' })}
            placeholder="Email"
            type="email"
            style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: 'none' }}
          />
          {errors.email && <p style={{ color: 'red' }}>{errors.email.message}</p>}
          <input
            {...register('password', {
              required: 'Password is required',
              validate: validatePassword
            })}
            placeholder="Password"
            type="password"
            style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px', border: 'none' }}
          />
          {errors.password && <p style={{ color: 'red' }}>{errors.password.message}</p>}
          <button
            type="submit"
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              marginBottom: '10px'
            }}
          >
            {isRegister ? 'Register' : 'Login'}
          </button>
        </form>
        <button
          onClick={() => setIsRegister(!isRegister)}
          style={{
            width: '100%',
            padding: '10px',
            backgroundColor: 'transparent',
            color: 'white',
            border: '1px solid white',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          {isRegister ? 'Already have an account? Login' : 'New user? Register'}
        </button>
      </div>
    </div>
  );
}

export default Login;
