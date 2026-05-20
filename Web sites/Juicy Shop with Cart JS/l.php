<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Интернет-магазин</title>

</head>

<style>
    body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  #catalog {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-around;
    width: 80%;
    margin-top: 20px;
  }
  
  .product-card {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    margin: 10px;
    width: 30%;
  }
  
  .cartitem__item-img{
    width: 60%;
    height: 60%;
  }

 #cart {
    position: fixed;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  #cart-icon img {
    width: 30px;
    height: 30px;
    margin-right: 5px;
  }
  
  #cart-count {
    background-color: #ff0000;
    color: #ffffff;
    padding: 5px;
    border-radius: 50%;
  }
  .item-card {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
  }
  #cart-items {
    background-color: #fff;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    max-height: 200px;
    width: 300px;
    overflow-y: auto;
  }
  .catalog__item-img {
  width: 60%;
  height: auto;
 }
</style>

<body>
<div id="catalog"></div>
<div id="cart">
  <div id="cart-icon">
    <img src="cart.png" alt="Cart">
    <span id="cart-count">0</span>
  </div>
  <div id="cart-items" style="display: none;"></div>
</div>

<script src="script.js"></script>
</body>
</html>
