import React from 'react';
import PropTypes from 'prop-types';
import { Icon } from 'antd';

function Button(props) {
  return <Icon type={props.icon} onClick={props.onClick} />;
}

Button.propTypes = {
  icon: PropTypes.string.isRequired,
  onClick: PropTypes.func,
};

export default Button;
