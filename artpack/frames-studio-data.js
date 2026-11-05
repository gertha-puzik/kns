const FRAMES_STUDIO_DATA = {
 "total": 43,
 "zones": [
  {
   "id": "eyes",
   "label": "Глаза (цвет глаз — выбор цвета, как в KNS CatWar)",
   "hex": "#000000"
  },
  {
   "id": "earL",
   "label": "Ухо 1 (левое на виде)",
   "hex": "#f48fb1"
  },
  {
   "id": "earR",
   "label": "Ухо 2 (правое на виде)",
   "hex": "#ff7043"
  },
  {
   "id": "nose",
   "label": "Нос + зона морды вокруг",
   "hex": "#ffeb3b"
  },
  {
   "id": "tail",
   "label": "Хвост",
   "hex": "#d32f2f"
  },
  {
   "id": "foreL",
   "label": "Передняя лапа (левая на виде)",
   "hex": "#2e7d32"
  },
  {
   "id": "foreR",
   "label": "Передняя лапа (правая на виде)",
   "hex": "#66bb6a"
  },
  {
   "id": "hindL",
   "label": "Задняя лапа/бедро (левое на виде)",
   "hex": "#01579b"
  },
  {
   "id": "hindR",
   "label": "Задняя лапа/бедро (правое на виде)",
   "hex": "#4fc3f7"
  },
  {
   "id": "head",
   "label": "Голова (без глаз/ушей/носа)",
   "hex": "#fbc02d"
  },
  {
   "id": "chest",
   "label": "Грудка (светлая зона спереди)",
   "hex": "#e1bee3"
  },
  {
   "id": "belly",
   "label": "Живот",
   "hex": "#b2dfdb"
  },
  {
   "id": "body",
   "label": "Тело (остаток)",
   "hex": "#7b1fa2"
  }
 ],
 "builds": {
  "norm": {
   "label": "Обычное телосложение",
   "frames": [
    {
     "name": "sit_norm.png",
     "src": "model/sit_norm.png",
     "key": "0",
     "label": "Сидит (родной M2)",
     "group": "Сид",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_norm_up_k0.png",
     "src": "model/walk_norm_up_k0.png",
     "key": "1",
     "label": "Ходьба вбок, фаза 0 (хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_norm_up_k1.png",
     "src": "model/walk_norm_up_k1.png",
     "key": "2",
     "label": "Ходьба вбок, фаза 1 (хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_norm_up_k2.png",
     "src": "model/walk_norm_up_k2.png",
     "key": "3",
     "label": "Ходьба вбок, фаза 2 (хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_norm_up_k3.png",
     "src": "model/walk_norm_up_k3.png",
     "key": "4",
     "label": "Ходьба вбок, фаза 3 (хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_norm_down_k0.png",
     "src": "model/walk_norm_down_k0.png",
     "key": null,
     "label": "Ходьба вбок, фаза 0 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_norm_down_k1.png",
     "src": "model/walk_norm_down_k1.png",
     "key": null,
     "label": "Ходьба вбок, фаза 1 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_norm_down_k2.png",
     "src": "model/walk_norm_down_k2.png",
     "key": null,
     "label": "Ходьба вбок, фаза 2 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_norm_down_k3.png",
     "src": "model/walk_norm_down_k3.png",
     "key": null,
     "label": "Ходьба вбок, фаза 3 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "E0.png",
     "src": "model/dirs/E0.png",
     "key": "E0",
     "label": "Вправо ×2, фаза 0",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "E1.png",
     "src": "model/dirs/E1.png",
     "key": "E1",
     "label": "Вправо ×2, фаза 1",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "E2.png",
     "src": "model/dirs/E2.png",
     "key": "E2",
     "label": "Вправо ×2, фаза 2",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "E3.png",
     "src": "model/dirs/E3.png",
     "key": "E3",
     "label": "Вправо ×2, фаза 3",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "W0.png",
     "src": "model/dirs/W0.png",
     "key": "W0",
     "label": "Влево ×2, фаза 0",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "W1.png",
     "src": "model/dirs/W1.png",
     "key": "W1",
     "label": "Влево ×2, фаза 1",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "W2.png",
     "src": "model/dirs/W2.png",
     "key": "W2",
     "label": "Влево ×2, фаза 2",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "W3.png",
     "src": "model/dirs/W3.png",
     "key": "W3",
     "label": "Влево ×2, фаза 3",
     "group": "Направления E/W/N/S",
     "w": 200,
     "h": 300,
     "hasMarkup": true
    },
    {
     "name": "N0.png",
     "src": "model/dirs/N0.png",
     "key": "N0",
     "label": "N (уход от камеры), фаза 0",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "N1.png",
     "src": "model/dirs/N1.png",
     "key": "N1",
     "label": "N (уход от камеры), фаза 1",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "N2.png",
     "src": "model/dirs/N2.png",
     "key": "N2",
     "label": "N (уход от камеры), фаза 2",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "N3.png",
     "src": "model/dirs/N3.png",
     "key": "N3",
     "label": "N (уход от камеры), фаза 3",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "S0.png",
     "src": "model/dirs/S0.png",
     "key": "S0",
     "label": "S (на камеру), фаза 0",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "S1.png",
     "src": "model/dirs/S1.png",
     "key": "S1",
     "label": "S (на камеру), фаза 1",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "S2.png",
     "src": "model/dirs/S2.png",
     "key": "S2",
     "label": "S (на камеру), фаза 2",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "S3.png",
     "src": "model/dirs/S3.png",
     "key": "S3",
     "label": "S (на камеру), фаза 3",
     "group": "Направления E/W/N/S",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    }
   ],
   "seqs": [
    {
     "group": "Сид",
     "frames": [
      "sit_norm.png"
     ]
    },
    {
     "group": "Ходьба (натив, хвост вверх)",
     "frames": [
      "walk_norm_up_k0.png",
      "walk_norm_up_k1.png",
      "walk_norm_up_k2.png",
      "walk_norm_up_k3.png"
     ]
    },
    {
     "group": "Ходьба (хвост вниз)",
     "frames": [
      "walk_norm_down_k0.png",
      "walk_norm_down_k1.png",
      "walk_norm_down_k2.png",
      "walk_norm_down_k3.png"
     ]
    },
    {
     "group": "Направления E/W/N/S · E",
     "frames": [
      "E0.png",
      "E1.png",
      "E2.png",
      "E3.png"
     ]
    },
    {
     "group": "Направления E/W/N/S · W",
     "frames": [
      "W0.png",
      "W1.png",
      "W2.png",
      "W3.png"
     ]
    },
    {
     "group": "Направления E/W/N/S · N",
     "frames": [
      "N0.png",
      "N1.png",
      "N2.png",
      "N3.png"
     ]
    },
    {
     "group": "Направления E/W/N/S · S",
     "frames": [
      "S0.png",
      "S1.png",
      "S2.png",
      "S3.png"
     ]
    }
   ]
  },
  "thin": {
   "label": "Худое",
   "frames": [
    {
     "name": "sit_thin.png",
     "src": "model/sit_thin.png",
     "key": "0",
     "label": "Сидит (худая)",
     "group": "Сид",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_thin_down_k0.png",
     "src": "model/walk_thin_down_k0.png",
     "key": "1",
     "label": "Ходьба, фаза 0 (натив: хвост вниз)",
     "group": "Ходьба (натив, хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_thin_down_k1.png",
     "src": "model/walk_thin_down_k1.png",
     "key": "2",
     "label": "Ходьба, фаза 1 (натив: хвост вниз)",
     "group": "Ходьба (натив, хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_thin_down_k2.png",
     "src": "model/walk_thin_down_k2.png",
     "key": "3",
     "label": "Ходьба, фаза 2 (натив: хвост вниз)",
     "group": "Ходьба (натив, хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_thin_down_k3.png",
     "src": "model/walk_thin_down_k3.png",
     "key": "4",
     "label": "Ходьба, фаза 3 (натив: хвост вниз)",
     "group": "Ходьба (натив, хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_thin_up_k0.png",
     "src": "model/walk_thin_up_k0.png",
     "key": null,
     "label": "Ходьба, фаза 0 (хвост вверх)",
     "group": "Ходьба (хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_thin_up_k1.png",
     "src": "model/walk_thin_up_k1.png",
     "key": null,
     "label": "Ходьба, фаза 1 (хвост вверх)",
     "group": "Ходьба (хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_thin_up_k2.png",
     "src": "model/walk_thin_up_k2.png",
     "key": null,
     "label": "Ходьба, фаза 2 (хвост вверх)",
     "group": "Ходьба (хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_thin_up_k3.png",
     "src": "model/walk_thin_up_k3.png",
     "key": null,
     "label": "Ходьба, фаза 3 (хвост вверх)",
     "group": "Ходьба (хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    }
   ],
   "seqs": [
    {
     "group": "Сид",
     "frames": [
      "sit_thin.png"
     ]
    },
    {
     "group": "Ходьба (натив, хвост вниз)",
     "frames": [
      "walk_thin_down_k0.png",
      "walk_thin_down_k1.png",
      "walk_thin_down_k2.png",
      "walk_thin_down_k3.png"
     ]
    },
    {
     "group": "Ходьба (хвост вверх)",
     "frames": [
      "walk_thin_up_k0.png",
      "walk_thin_up_k1.png",
      "walk_thin_up_k2.png",
      "walk_thin_up_k3.png"
     ]
    }
   ]
  },
  "chub": {
   "label": "Пухлое",
   "frames": [
    {
     "name": "sit_chub.png",
     "src": "model/sit_chub.png",
     "key": "0",
     "label": "Сидит (пухлая)",
     "group": "Сид",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_chub_up_k0.png",
     "src": "model/walk_chub_up_k0.png",
     "key": "1",
     "label": "Ходьба, фаза 0 (натив: хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_chub_up_k1.png",
     "src": "model/walk_chub_up_k1.png",
     "key": "2",
     "label": "Ходьба, фаза 1 (натив: хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_chub_up_k2.png",
     "src": "model/walk_chub_up_k2.png",
     "key": "3",
     "label": "Ходьба, фаза 2 (натив: хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_chub_up_k3.png",
     "src": "model/walk_chub_up_k3.png",
     "key": "4",
     "label": "Ходьба, фаза 3 (натив: хвост вверх)",
     "group": "Ходьба (натив, хвост вверх)",
     "w": 100,
     "h": 150,
     "hasMarkup": true
    },
    {
     "name": "walk_chub_down_k0.png",
     "src": "model/walk_chub_down_k0.png",
     "key": null,
     "label": "Ходьба, фаза 0 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_chub_down_k1.png",
     "src": "model/walk_chub_down_k1.png",
     "key": null,
     "label": "Ходьба, фаза 1 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_chub_down_k2.png",
     "src": "model/walk_chub_down_k2.png",
     "key": null,
     "label": "Ходьба, фаза 2 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    },
    {
     "name": "walk_chub_down_k3.png",
     "src": "model/walk_chub_down_k3.png",
     "key": null,
     "label": "Ходьба, фаза 3 (хвост вниз)",
     "group": "Ходьба (хвост вниз)",
     "w": 100,
     "h": 150,
     "hasMarkup": false
    }
   ],
   "seqs": [
    {
     "group": "Сид",
     "frames": [
      "sit_chub.png"
     ]
    },
    {
     "group": "Ходьба (натив, хвост вверх)",
     "frames": [
      "walk_chub_up_k0.png",
      "walk_chub_up_k1.png",
      "walk_chub_up_k2.png",
      "walk_chub_up_k3.png"
     ]
    },
    {
     "group": "Ходьба (хвост вниз)",
     "frames": [
      "walk_chub_down_k0.png",
      "walk_chub_down_k1.png",
      "walk_chub_down_k2.png",
      "walk_chub_down_k3.png"
     ]
    }
   ]
  }
 }
};
