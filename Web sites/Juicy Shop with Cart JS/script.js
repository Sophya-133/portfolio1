const products = [
  { id: 1, name: 'Juicy Life Смузи', description: 'В состав входят киви, ананас, яблоко, апельсин','image':'./img/смузи-киви.jpg', price: 57 },
  { id: 2, name: 'Лесной смузи', description: 'В состав входят ежевика, черника, голубика, чёрная смородина.', 'image':'./img/черника.jpg',price: 62 },
  { id: 3, name: 'Клубничный рай', description: 'В состав входят клубника, земляника, гуава.','image':'./img/смузи-клубника.jpg', price: 48 },
  { id: 4, name: 'Бодрящий смузи', description:'В состав входят огурец, сельдерей, укроп, помидор.','image':'./img/смузи-огурец.png', price: 39 },
  { id: 5, name: 'Свекольная радость', description: 'В состав входят свёкла, морковь, сельдерей.','image':'./img/смузи-свекла.jpg', price: 49.99 },
  { id: 6, name: 'Тыквенное наслаждение', description: 'В состав входят тыква, морковь, имбирь, банан.','image':'./img/смузи-тыква.jpg', price: 43 },
  { id: 7, name: 'Юный персик', description: 'В состав входят мякоть персика, имбирь, маракуйя, груша.','image':'./img/смузи-персик.jpg', price: 63 },
  { id: 8, name: 'Пикантный сливовый смузи', description: 'В состав входят слива, банан, шпинат, мёд.','image':'./img/смузи-слива.jpg', price: 45 },
  { id: 9, name: 'Жиросжигающий грейпфрутовый смузи', description: 'В состав входят грейпфрут, киви, семена льна, отруби, мята.','image':'./img/смузи-грейпфрут.jpeg', price: 57 }
];

 document.addEventListener('DOMContentLoaded', function() {//Запуск после загрузки html страницы
  const catalog = document.getElementById('catalog');// каталог товаров
  const cartCount = document.getElementById('cart-count');//индекс над корзиной
  const cartItems = document.getElementById('cart-items');//товары в корзине

  products.forEach(product => {//для каждого товара создается карточка
    const productCard = document.createElement('div');//создаём элемент div (контейнер) для каталога товаров
    productCard.classList.add('product-card');//добавляем в div класс product-card(чтобы задать css стиль)
    // Вставка html элементов для карточки товара(имя,характеристика,фото,цена)
    productCard.innerHTML = `
      <h3>${product.name}</h3>
      <p>${product.description}</p>
      <img src="${product.image}" class="catalog__item-img" alt="${product.name}">
      <p>Цена: ${product.price} р.</p>
      <button class="add-to-cart" data-id="${product.id}">Добавить в корзину</button>
    `;//кнопка добавить(id кнопки такое же какое id товара)
    catalog.appendChild(productCard);//добавляем карточку товара как дочерний элемент в каталог товаров
  });

  let cartTotal = 0;// общее кол-во товаров индекс корзины
  let cartItemsList = {};// товары в корзине

  catalog.addEventListener('click', function(event) {// обработчик события клика 
    if (event.target.classList.contains('add-to-cart')) {// проверяем была ли нажата именно кнопка добавить в корзину
      const productId = event.target.getAttribute('data-id');// если да получаем id кнопки(такое же id товара)
      cartTotal++;// увеличиваем общее кол-во на один
      cartCount.textContent = cartTotal;// Записываем новое значение в индекс корзины

      if (productId in cartItemsList) {//если товар с таким id(нажатый на добавить) уже есть в корзине
        cartItemsList[productId].quantity++;//увеличиваем графу кол-во на 1
        cartItemsList[productId].price = products.find(product => product.id == productId).price * cartItemsList[productId].quantity;//пересчитываем стоимость товара(цена товара*на записанное новое кол-во)
      } else {
        cartItemsList[productId] = {// если не было товара
          ...products.find(product => product.id == productId),//находим товар с таким id(копируем его свойства)
          quantity: 1// Ставим кол-во один
        };
      }
      renderCartItems();//Отрисовка самих карточек в корзине
    }
  });

  function renderCartItems() {//Отрисовка корзины
    cartItems.innerHTML = '';//Очищаем корзину

    for (const key in cartItemsList) {//перебирает все ключи в объекте (списке товаров в корзине)
      const item = cartItemsList[key];//получает товар (текущий) по ключу(индекс) 
      const itemCard = document.createElement('div');//Создаем контейнер div для списка корзины
      itemCard.classList.add('item-card');//Создаем класс item-card для установления css для контейнера всего списка
      //Карточки товаров корзины(html)
      itemCard.innerHTML = `
        <h3>${item.name}</h3>
        <p>${item.description}</p>
        <p>Кол-во: ${item.quantity}</p>
        <img class="cartitem__item-img" src="${item.image}" alt="${item.name}">
        <p>Цена:${item.price} р.</p>
        <button class="remove-from-cart" data-id="${item.id}">Удалить из корзины</button>
      `;
      //Кнопка удалить(id такой же как и у товара в корзине)
      cartItems.appendChild(itemCard);//добавляем карточку товара как дочерний элемент в списке всех товаров в корзине
    }

    const totalPrice = Object.values(cartItemsList).reduce((acc, item) => acc + item.price, 0);//Итоговая стоимость(сумма цен всех товаров). acc-общая стоимость(изначально=0).item.price(цена товара)
    cartItems.innerHTML += `<p>Итоговая цена: ${totalPrice} р.</p>`;//Выводим html итоговая стоимость=
  }

  cart.addEventListener('click', function(event) {// Обработка клика по элементу
    if (event.target.id === 'cart-icon') {//если нажали по иконке корзины
      cartItems.style.display = cartItems.style.display === 'none' ? 'block' : 'none';//если просто иконка,то раскрывается список карточек.если уже был список,корзина сворачивается
    }

    if (event.target.classList.contains('remove-from-cart')) {//Удаление из корзины
      const productId = event.target.getAttribute('data-id');//Получаем id кнопки(товара)
      cartTotal -= cartItemsList[productId].quantity;//вычитаем кол-во этого товара(по id) из общего кол-ва (счетчика корзины)
      cartCount.textContent = cartTotal;// Записываем новое кол-во в счетчик корзины
      delete cartItemsList[productId];//Удаляем из списка товаров корзины выбранный товар

      renderCartItems();//Перерисовываем корзину с учетом изменений
    }
  });
});
