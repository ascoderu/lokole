import React from 'react';
import { List } from 'antd';

function Grid(props) {
  return (
    <List
      grid={{ gutter: 16, xs: 1, md: 4, lg: 6 }}
      itemLayout="vertical"
      {...props}
    />
  );
}

export default Grid;
