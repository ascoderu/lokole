import React from 'react';
import { Icon } from 'antd';

function Button(props) {
  return <Icon type={props.icon} onClick={props.onClick} />;
}

export default Button;
