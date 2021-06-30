#pragma once

#include "dockhandler.h"
#include "render.h"
#include "uitypes.h"

class BINARYNINJAUIAPI StackView : public QWidget, public DockContextHandler {
    Q_OBJECT
    Q_INTERFACES(DockContextHandler)

    ViewFrame* m_view;
    BinaryViewRef m_data;
    FunctionRef m_func;
    RenderContext m_renderer;

    //! Get a list of DisassemblyTextLines that represent the stack layout.
    std::vector<BinaryNinja::DisassemblyTextLine> lines();

protected:
    void paintEvent(QPaintEvent* event);

public:
    StackView(ViewFrame* view, BinaryViewRef data);

    //! Refresh the stack view's content.
    void refresh();
};
