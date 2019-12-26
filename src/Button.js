import React from 'react';
import { Icon, Tooltip } from 'antd';

function Button({ onClick, icon, label }) {
  return (
    <Tooltip title={label}>
      <Icon
        type={icon}
        onClick={onClick}
      />
    </Tooltip>
  );
}

export default Button;
