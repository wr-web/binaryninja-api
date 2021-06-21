#pragma once

#include "binaryninjaapi.h"
#include "uicontext.h"
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QRadioButton>

class BINARYNINJAUIAPI CompileOptions : public QDialog
{
	Q_OBJECT

	QCheckBox* m_safeStack;
	QLineEdit* m_blacklist;
	QLineEdit* m_base;
	QLineEdit* m_maxLength;
	QCheckBox* m_pad;
	QCheckBox* m_polymorph;

	QRadioButton* m_exit;
	QRadioButton* m_allowReturn;
	QRadioButton* m_concat;

	QLineEdit* m_stackReg;
	QLineEdit* m_frameReg;
	QLineEdit* m_baseReg;
	QLineEdit* m_returnReg;
	QLineEdit* m_returnHighReg;
	QCheckBox* m_encodePointers;
	QCheckBox* m_stackGrowsUp;
	QCheckBox* m_antiDisasm;
	QLineEdit* m_antiDisasmFreq;
	QLineEdit* m_seed;

	QString optionValue(const std::map<std::string, std::string>& options, const std::string& name);
	void updateOptions(const std::map<std::string, std::string>& options);

 public:
	CompileOptions(QWidget* parent, const std::map<std::string, std::string>& initialOptions);

	std::map<std::string, std::string> getSettings();

 private Q_SLOTS:
	void reset();
};
